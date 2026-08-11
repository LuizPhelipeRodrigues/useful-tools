import streamlit as st

class CHBAtualizacoes():
  def parse_updates(self, body_email):
    start = body_email.find("NOTIFICAÇ�?O")
    startpoint = (start if start > -1 else 0) + len("NOTIFICAÇ�?O")
    end = body_email.find("*******", startpoint)
    
    parsed_updates = body_email[startpoint:end]
    updates = [update.strip() for update in parsed_updates.split("\n") if update.strip()]
    return "\n".join(updates)