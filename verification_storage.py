import json
import os
from datetime import datetime
import pytz
from typing import Dict, List, Any


class VerificationStorage:

    def __init__(self, filename: str = "verificacao.json"):
        self.filename = filename
        self.ensure_file_exists()

    def ensure_file_exists(self):
        """Garante que o arquivo JSON existe"""
        if not os.path.exists(self.filename):
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump({"verificacoes": []},
                          f,
                          ensure_ascii=False,
                          indent=2)

    def save_verification(self, user_data: Dict[str, Any]) -> bool:
        """Salva dados de verificação de um usuário"""
        try:
            # Ler dados existentes
            with open(self.filename, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Verificar se usuário já existe
            user_id = user_data.get('user_id')
            existing_index = None

            for i, verification in enumerate(data["verificacoes"]):
                if verification.get('user_id') == user_id:
                    existing_index = i
                    break

            # Adicionar timestamp com horário de Brasília
            brasilia_tz = pytz.timezone('America/Sao_Paulo')
            now_brasilia = datetime.now(brasilia_tz)
            user_data['data'] = now_brasilia.strftime(
                "%d/%m/%Y às %H:%M:%S (Brasília)")
            user_data['timestamp'] = now_brasilia.isoformat()

            # Atualizar ou adicionar
            if existing_index is not None:
                data["verificacoes"][existing_index] = user_data
            else:
                data["verificacoes"].append(user_data)

            # Salvar de volta
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return True
        except Exception as e:
            print(f"Erro ao salvar verificação: {e}")
            return False

    def get_all_verifications(self) -> List[Dict[str, Any]]:
        """Retorna todas as verificações salvas"""
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get("verificacoes", [])
        except Exception as e:
            print(f"Erro ao carregar verificações: {e}")
            return []

    def get_verification_by_user(self, user_id: int) -> Dict[str, Any] | None:
        """Busca verificação específica pelo ID do usuário"""
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for verification in data.get("verificacoes", []):
                if verification.get("user_id") == user_id:
                    return verification

            return None
        except Exception as e:
            print(f"Erro ao buscar verificação: {e}")
            return None

    def count_verifications(self) -> int:
        """Conta o total de verificações"""
        try:
            verifications = self.get_all_verifications()
            return len(verifications)
        except Exception as e:
            print(f"Erro ao contar verificações: {e}")
            return 0

    def get_recent_verifications(self,
                                 limit: int = 10) -> List[Dict[str, Any]]:
        """Retorna as verificações mais recentes"""
        try:
            all_verifications = self.get_all_verifications()
            # Ordenar por timestamp (mais recente primeiro)
            sorted_verifications = sorted(all_verifications,
                                          key=lambda x: x.get('timestamp', ''),
                                          reverse=True)
            return sorted_verifications[:limit]
        except Exception as e:
            print(f"Erro ao buscar verificações recentes: {e}")
            return []