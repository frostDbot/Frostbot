import json
import os
from datetime import datetime
import pytz
from typing import Dict, List, Any


class EventStorage:

    def __init__(self, filename: str = "eventos.json"):
        self.filename = filename
        self.ensure_file_exists()

    def ensure_file_exists(self):
        """Garante que o arquivo JSON existe"""
        if not os.path.exists(self.filename):
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump({"eventos": []}, f, ensure_ascii=False, indent=2)

    def save_event(self, event_data: Dict[str, Any]) -> bool:
        """Salva um evento no arquivo JSON"""
        try:
            # Ler dados existentes
            with open(self.filename, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Adicionar timestamp se não existir
            if 'timestamp' not in event_data:
                brasilia_tz = pytz.timezone('America/Sao_Paulo')
                now_brasilia = datetime.now(brasilia_tz)
                event_data['timestamp'] = now_brasilia.isoformat()
                event_data['data_brasilia'] = now_brasilia.strftime(
                    "%d/%m/%Y às %H:%M:%S (Brasília)")

            # Adicionar o novo evento
            data["eventos"].append(event_data)

            # Verificar se chegou a 50 eventos e fazer limpeza
            if len(data["eventos"]) >= 50:
                print(
                    f"Limite de 50 eventos atingido. Limpando eventos antigos..."
                )
                # Manter apenas os 25 mais recentes
                data["eventos"] = data["eventos"][-25:]
                print(
                    f"Limpeza concluída. Mantidos {len(data['eventos'])} eventos mais recentes."
                )

            # Salvar de volta
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return True
        except Exception as e:
            print(f"Erro ao salvar evento: {e}")
            return False

    def get_recent_events(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Retorna os eventos mais recentes"""
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Retornar os últimos eventos (mais recentes primeiro)
            eventos = data.get("eventos", [])
            return eventos[-limit:][::-1]  # Últimos N, invertidos
        except Exception as e:
            print(f"Erro ao carregar eventos: {e}")
            return []

    def update_event_participants(self, event_id: str,
                                  participants_data: Dict[str, Any]) -> bool:
        """Atualiza os participantes de um evento específico"""
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Encontrar e atualizar o evento
            for evento in data["eventos"]:
                if evento.get("event_id") == event_id:
                    evento["participantes"] = participants_data
                    brasilia_tz = pytz.timezone('America/Sao_Paulo')
                    now_brasilia = datetime.now(brasilia_tz)
                    evento["ultima_atualizacao"] = now_brasilia.isoformat()
                    evento[
                        "ultima_atualizacao_brasilia"] = now_brasilia.strftime(
                            "%d/%m/%Y às %H:%M:%S (Brasília)")
                    break

            # Salvar de volta
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return True
        except Exception as e:
            print(f"Erro ao atualizar participantes: {e}")
            return False

    def get_event_by_id(self, event_id: str) -> Dict[str, Any] | None:
        """Busca um evento específico pelo ID"""
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for evento in data.get("eventos", []):
                if evento.get("event_id") == event_id:
                    return evento

            return None
        except Exception as e:
            print(f"Erro ao buscar evento: {e}")
            return None

    def cleanup_old_events(self, keep_count: int = 25) -> bool:
        """Remove eventos antigos mantendo apenas os mais recentes"""
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                data = json.load(f)

            eventos_antes = len(data.get("eventos", []))

            if eventos_antes > keep_count:
                data["eventos"] = data["eventos"][-keep_count:]

                with open(self.filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

                eventos_removidos = eventos_antes - len(data["eventos"])
                print(
                    f"Limpeza manual: {eventos_removidos} eventos antigos removidos. Mantidos: {len(data['eventos'])}"
                )
                return True
            else:
                print(
                    f"Nenhuma limpeza necessária. Total de eventos: {eventos_antes}"
                )
                return True

        except Exception as e:
            print(f"Erro ao limpar eventos antigos: {e}")
            return False

    def delete_events(self, event_ids: List[str]) -> bool:
        """Deleta eventos específicos pelos seus IDs"""
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                data = json.load(f)

            eventos_antes = len(data.get("eventos", []))

            # Filtrar eventos que não estão na lista de IDs para deletar
            data["eventos"] = [
                evento for evento in data["eventos"]
                if evento.get("event_id") not in event_ids
            ]

            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            eventos_removidos = eventos_antes - len(data["eventos"])
            print(
                f"Deletados {eventos_removidos} eventos. Restam: {len(data['eventos'])}"
            )
            return True

        except Exception as e:
            print(f"Erro ao deletar eventos: {e}")
            return False

    def get_all_events(self) -> List[Dict[str, Any]]:
        """Retorna todos os eventos salvos"""
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get("eventos", [])
        except Exception as e:
            print(f"Erro ao carregar todos os eventos: {e}")
            return []