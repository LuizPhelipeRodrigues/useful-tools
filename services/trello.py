import re
import io
import pandas as pd
from datetime import datetime, timezone, timedelta, date

BRASILIA = timezone(timedelta(hours=-3))
TYPE_KEYWORDS = {"EVOLUTIVA", "CORREÇÃO"}
DONE_KEYWORDS = {
  "concluído", "concluida", "concluídos", "concluidas",
  "done", "finalizado", "finalizados", "finished", "completo", "completos",
}

class Trello():
    def parse_date(self, date_str: str | None) -> datetime | None:
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except ValueError:
            return None

    def format_date(self, dt: datetime | None) -> str:
        if dt is None:
            return ""
        local = dt.astimezone(BRASILIA)
        return local.strftime("%d/%m/%Y %H:%M")

    def format_date_short(self, dt: datetime | None) -> str:
        if dt is None:
            return ""
        local = dt.astimezone(BRASILIA)
        return local.strftime("%d/%m/%Y")
    
    def get_title(self, title: str, sector: str | None) -> str:
      if sector is not None:
        return title.replace(str(sector + ":"), "")
      else:
        return title

    def extract_title(self, title: str) -> tuple:
        m = re.match(r"^\[(.+?)\]", title)
        if m:
            sector = m.group(1).strip()
            if len(sector) <= 30:
                if sector == "REALIZADA" or sector == "PENDENTE":
                    return self.get_title(title, ""), "" 
            return self.get_title(title, sector), sector 

        m = re.match(r"^([A-ZÀ-Ú][^:\-]{0,28})[\s]*[-:][\s]", title)
        if m:
            sector = m.group(1).strip()
            if len(sector) <= 30:
                if sector == "REALIZADA" or sector == "PENDENTE":
                    return self.get_title(title, ""), ""
                return self.get_title(title, sector), sector

        return self.get_title(title, None), "—" 
    
    def build_observation(self, status: str, done_date: datetime | None, obs: str) -> str:
        if status == "CONCLUÍDO":
            date_str = self.format_date_short(done_date) if done_date else "data não registrada"
            return f"Concluído no dia {date_str}"

        # Não concluído → usa descrição se houver
        return obs if len(obs) > 12 else ""

    def extract_desc(self, desc: str, status: str, done_date: datetime | None) -> tuple:
      pos_desc_label = desc.find("[DESCRICAO]:")
      pos_desc_content = (pos_desc_label if pos_desc_label > -1 else 0) + len("[DESCRICAO]:") 
    
      pos_obs_label = desc.find("[OBSERVACAO]:")
    
      description = desc[pos_desc_content:pos_obs_label].strip() or ""
      observation = self.build_observation(status, done_date, desc[pos_obs_label:].strip()) or ""

      return description, observation
    
    def find_done_list_ids(self, lists: list[dict]) -> set[str]:
        done_ids = set()
        for lst in lists:
            name = lst.get("name", "").lower().strip()
            if name in DONE_KEYWORDS or any(kw in name for kw in DONE_KEYWORDS):
                done_ids.add(lst["id"])
        return done_ids
    
    def get_done_date(self, card: dict, actions: list[dict], done_list_ids: set[str]) -> datetime | None:
        card_id = card["id"]

        # 1. Ação de mover para lista done
        for action in actions:
            if action.get("type") != "updateCard":
                continue
            if action.get("data", {}).get("card", {}).get("id") != card_id:
                continue
            after = action.get("data", {}).get("listAfter", {})
            if after.get("id") in done_list_ids:
                return self.parse_date(action.get("date"))

        # 2. dueComplete + due
        if card.get("dueComplete") and card.get("due"):
            return self.parse_date(card["due"])

        # 3. Cartão já está na lista done → dateLastActivity
        if card.get("idList") in done_list_ids:
            return self.parse_date(card.get("dateLastActivity"))

        return None

    def get_status(self, card: dict, done_list_ids: set[str]) -> str:
        labels = card.get("labels", [])
        if labels:
            for label in labels:
                name = label.get("name", "").strip()
                if name not in TYPE_KEYWORDS or not any(kw in name for kw in TYPE_KEYWORDS):
                    return name.upper() if name else "SEM ETIQUETA"
            return "PENDENTE" 
        if card.get("idList") in done_list_ids or card.get("dueComplete"):
            return "CONCLUÍDO"
        return "PENDENTE"

    def get_type(self, card: dict) -> str:
        labels = card.get("labels", [])
        if labels:
            for label in labels:
                name = label.get("name", "").strip()
                if name in TYPE_KEYWORDS or any(kw in name for kw in TYPE_KEYWORDS):
                    return name
        return ""
    
    def process_trello_json(self, data: dict, initial_date: date, final_date: date) -> list[dict]:
        lists = data.get("lists", [])
        cards = data.get("cards", [])
        actions = data.get("actions", [])

        done_list_ids = self.find_done_list_ids(lists)
        results = []

        for card in cards:
            card_title = card.get("name", "").strip()
            card_description = card.get("desc", "").strip()

            done_date = self.get_done_date(card, actions, done_list_ids)
            status = self.get_status(card, done_list_ids)
            type_card = self.get_type(card) 

            # Filtro de datas — usa done_date se existir, senão dateLastActivity
            ref_dt = done_date or self.parse_date(card.get("dateLastActivity"))
            if ref_dt:
                ref_local = ref_dt.astimezone(BRASILIA).date()
                if not (initial_date <= ref_local <= final_date):
                    continue
                
            # Extrai o título e o setor que solicitou o atendimento do título do cartão
            title, sector = self.extract_title(card_title)
            description, observation = self.extract_desc(card_description, status, done_date)

            results.append({
                "Data": self.format_date(done_date),
                "Atividade Realizada": title,
                "Descrição da Atividade": description,
                "Tipo": type_card,
                "Setor": sector,
                "Status": status,
                "Observação": observation,
            })

        return results

    def to_excel(self, df: pd.DataFrame) -> bytes:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Atividades")

            ws = writer.sheets["Atividades"]

            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

            header_fill = PatternFill("solid", fgColor="DA9694")
            header_font = Font(bold=True, color="FFFFFF", size=10)
            thin = Side(style="thin", color="CCCCCC")
            border = Border(left=thin, right=thin, top=thin, bottom=thin)

            col_widths = {"A": 20, "B": 40, "C": 45, "D": 18, "E": 14, "F": 42}
            for col, width in col_widths.items():
                ws.column_dimensions[col].width = width

            for cell in ws[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center", vertical="center")
                cell.border = border

            ws.row_dimensions[1].height = 24

            for row in ws.iter_rows(min_row=2):
                status_cell = row[4]  # coluna E
                for cell in row:
                    cell.border = border
                    cell.alignment = Alignment(vertical="top", wrap_text=True)
                ws.row_dimensions[status_cell.row].height = 36

            ws.auto_filter.ref = ws.dimensions
            ws.freeze_panes = "A2"

        return output.getvalue()

    def status_badge(self, status: str) -> str:
        cls = "badge-done" if status == "CONCLUÍDO" else ("badge-pending" if status == "PENDENTE" else "badge-other")
        return f'<span class="badge {cls}">{status}</span>'