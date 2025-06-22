import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import datetime
import pytz
import uuid
from storage import EventStorage


class EnqueteView(discord.ui.View):

    def __init__(self, bot, enquete_data, limites):
        super().__init__(timeout=None)
        self.bot = bot
        self.enquete_data = enquete_data
        self.limites = limites
        self.votos = {'TANKER': [], 'HEALER': [], 'DPS': [], 'RESERVA': []}
        self.user_votes = {}
        self.storage = EventStorage()

        # Emojis para cada tipo
        self.emojis = {
            'TANKER': '🛡️',
            'HEALER': '🚑',
            'DPS': '⚔️',
            'RESERVA': '🔄'
        }

        # Ordem específica
        ordem_tipos = ['TANKER', 'HEALER', 'DPS', 'RESERVA']

        # Adicionar botões para cada tipo na ordem especificada
        for tipo in ordem_tipos:
            if tipo in limites and limites[tipo] > 0:
                button = discord.ui.Button(label=f"{tipo} (0/{limites[tipo]})",
                                           emoji=self.emojis[tipo],
                                           style=discord.ButtonStyle.secondary,
                                           custom_id=f"vote_{tipo}")
                button.callback = self.make_vote_callback(tipo)
                self.add_item(button)

    def make_vote_callback(self, tipo):

        async def vote_callback(interaction):
            await self.processar_voto(interaction, tipo)

        return vote_callback

    async def processar_voto(self, interaction, tipo):
        try:
            user_id = interaction.user.id

            # Verificar se já votou em algum tipo
            if user_id in self.user_votes:
                tipo_anterior = self.user_votes[user_id]
                if tipo_anterior == tipo:
                    # Permitir desmarcar a própria seleção
                    self.votos[tipo].remove(user_id)
                    del self.user_votes[user_id]

                    await interaction.response.send_message(
                        f"✅ Você foi removido da categoria **{tipo}** {self.emojis[tipo]}!",
                        ephemeral=True)

                    # Salvar participantes no JSON
                    await self.salvar_participantes()

                    # Atualizar os botões após responder
                    await self.atualizar_botoes_followup(interaction)
                    return

                # Remover voto anterior
                if user_id in self.votos[tipo_anterior]:
                    self.votos[tipo_anterior].remove(user_id)

            # Verificar se o tipo atingiu o limite
            if len(self.votos[tipo]) >= self.limites[tipo]:
                await interaction.response.send_message(
                    f"❌ A categoria **{tipo}** já atingiu o limite de {self.limites[tipo]} jogadores!",
                    ephemeral=True)
                return

            # Adicionar novo voto
            self.votos[tipo].append(user_id)
            self.user_votes[user_id] = tipo

            await interaction.response.send_message(
                f"✅ Você foi registrado como **{tipo}** {self.emojis[tipo]}!",
                ephemeral=True)

            # Salvar participantes no JSON
            await self.salvar_participantes()

            # Atualizar os botões após responder
            await self.atualizar_botoes_followup(interaction)

        except Exception as e:
            print(f"Erro ao processar voto: {e}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        "❌ Erro ao processar seu voto. Tente novamente!",
                        ephemeral=True)
                else:
                    await interaction.followup.send(
                        "❌ Erro ao processar seu voto. Tente novamente!",
                        ephemeral=True)
            except:
                pass

    async def salvar_participantes(self):
        """Salva os participantes atuais no JSON com nickname do servidor"""
        try:
            # Preparar dados dos participantes com nomes do servidor
            participantes_data = {}

            for tipo, user_ids in self.votos.items():
                participantes_data[tipo] = []
                for user_id in user_ids:
                    try:
                        # Buscar o servidor correto de forma mais robusta
                        guild = None

                        # Primeiro: tentar encontrar o servidor pelo canal onde foi criada a enquete
                        for bot_guild in self.bot.guilds:
                            for channel in bot_guild.channels:
                                if channel.id == self.enquete_data['canal_id']:
                                    guild = bot_guild
                                    print(
                                        f"🔍 Servidor encontrado: {guild.name} (ID: {guild.id})"
                                    )
                                    break
                            if guild:
                                break

                        member = None
                        nome_servidor = None

                        if guild:
                            member = guild.get_member(user_id)
                            if member:
                                print(
                                    f"Membro encontrado: {member.name}, display_name: {member.display_name}, nick: {member.nick}"
                                )
                                # PRIORIDADE 1: Nickname específico do servidor (se existir)
                                if member.nick:
                                    nome_servidor = member.nick
                                    print(
                                        f"✅ Salvando NICKNAME DO SERVIDOR: '{member.nick}' para user {user_id}"
                                    )
                                # PRIORIDADE 2: Nome global do Discord (se não tiver nickname)
                                else:
                                    nome_servidor = member.global_name or member.name
                                    print(
                                        f"⚠️ Salvando nome global: '{nome_servidor}' para user {user_id} (SEM nickname no servidor)"
                                    )
                            else:
                                print(
                                    f"❌ Membro {user_id} não encontrado no servidor {guild.name}"
                                )

                        # Se não conseguiu pegar como membro, tentar como usuário global
                        if not nome_servidor:
                            user = self.bot.get_user(user_id)
                            if not user:
                                user = await self.bot.fetch_user(user_id)

                            if user:
                                nome_servidor = user.global_name or user.name
                            else:
                                nome_servidor = "Usuário não encontrado"

                        # Salvar com informações detalhadas
                        participante_info = {
                            "user_id": user_id,
                            "nome": nome_servidor,
                            "nome_servidor":
                            nome_servidor  # Campo específico para o nome no servidor
                        }

                        # Se encontrou o membro, salvar informações adicionais para debug
                        if guild:
                            member = guild.get_member(user_id)
                            if member:
                                participante_info["tem_nickname"] = bool(
                                    member.nick)
                                participante_info[
                                    "nickname_atual"] = member.nick
                                participante_info[
                                    "nome_global"] = member.global_name or member.name

                        participantes_data[tipo].append(participante_info)
                        print(f"💾 Participante salvo: {participante_info}")

                    except Exception as e:
                        print(
                            f"Erro ao buscar dados do usuário {user_id}: {e}")
                        participantes_data[tipo].append({
                            "user_id":
                            user_id,
                            "nome":
                            "Usuário não encontrado",
                            "nome_servidor":
                            "Usuário não encontrado"
                        })

            # Atualizar no storage
            self.storage.update_event_participants(
                self.enquete_data['event_id'], participantes_data)

        except Exception as e:
            print(f"Erro ao salvar participantes: {e}")

    async def atualizar_botoes_followup(self, interaction):
        try:
            await asyncio.sleep(0.5)

            user_id = interaction.user.id
            user_selected_tipo = self.user_votes.get(user_id)

            # Atualizar labels dos botões
            for item in self.children:
                if isinstance(item, discord.ui.Button):
                    tipo = item.custom_id.split('_')[1]
                    atual = len(self.votos[tipo])
                    limite = self.limites[tipo]
                    item.label = f"{tipo} ({atual}/{limite})"

                    # Lógica de cores e estados dos botões
                    if atual >= limite:
                        # Tipo atingiu o limite
                        if user_selected_tipo == tipo:
                            # Usuário está neste tipo que atingiu o limite - mostrar em verde
                            item.style = discord.ButtonStyle.success
                            item.disabled = False  # Permitir que desmarque
                        else:
                            # Tipo cheio e usuário não está nele - desabilitar
                            item.style = discord.ButtonStyle.success
                            item.disabled = True
                    else:
                        # Tipo ainda tem vagas
                        if user_selected_tipo == tipo:
                            # Usuário selecionou este tipo - mostrar em verde
                            item.style = discord.ButtonStyle.success
                            item.disabled = False
                        else:
                            # Tipo disponível mas usuário não selecionou - mostrar normal
                            item.style = discord.ButtonStyle.secondary
                            item.disabled = False

            # Calcular totais
            total_vagas = 0
            total_registrados = 0
            ordem_tipos = ['TANKER', 'HEALER', 'DPS', 'RESERVA']

            for tipo in ordem_tipos:
                if tipo in self.limites and self.limites[tipo] > 0:
                    atual = len(self.votos[tipo])
                    limite = self.limites[tipo]
                    total_vagas += limite
                    total_registrados += atual

            # Verificar se a enquete está completa
            enquete_completa = total_registrados >= total_vagas

            # Atualizar o embed
            if enquete_completa:
                # Embed de resultado final
                embed = discord.Embed(
                    title=f"✅ EVENTO COMPLETO: {self.enquete_data['titulo']}",
                    color=discord.Color.green())

                descricao = f"**📅 Horário:** {self.enquete_data['horario']}\n\n"
                descricao += f"**📜 ** {self.enquete_data['levar']}\n\n"
                descricao += "**🎉 LISTA FINAL DOS PARTICIPANTES:**\n\n"

                for tipo in ordem_tipos:
                    if tipo in self.limites and self.limites[tipo] > 0:
                        emoji = self.emojis[tipo]
                        users = self.votos.get(tipo, [])
                        limite = self.limites[tipo]

                        descricao += f"{emoji} **{tipo}** ({len(users)}/{limite}):\n"

                        if users:
                            for user_id in users:
                                try:
                                    # PRIORIDADE 1: Tentar buscar membro atual do servidor para pegar o nickname do servidor
                                    member = interaction.guild.get_member(
                                        user_id)
                                    if member:
                                        # PRIORIDADE 1: Nickname específico do servidor
                                        if member.nick:
                                            descricao += f"   • {member.nick}\n"
                                            continue
                                        # PRIORIDADE 2: Nome global do Discord
                                        else:
                                            descricao += f"   • {member.global_name or member.name}\n"
                                            continue

                                    # PRIORIDADE 2: Buscar dados salvos no evento (nickname que estava no servidor na época)
                                    nome_salvo = None
                                    event_data = self.storage.get_event_by_id(
                                        self.enquete_data['event_id'])
                                    if event_data and 'participantes' in event_data:
                                        for participante in event_data[
                                                'participantes'].get(tipo, []):
                                            if participante.get(
                                                    'user_id') == user_id:
                                                nome_salvo = participante.get(
                                                    'nome_servidor'
                                                ) or participante.get('nome')
                                                break

                                    if nome_salvo:
                                        descricao += f"   • {nome_salvo} (não está mais no servidor)\n"
                                        continue

                                    # PRIORIDADE 3: Último fallback se não conseguiu encontrar
                                    descricao += f"   • Usuário saiu do servidor\n"

                                except Exception as e:
                                    print(
                                        f"Erro ao buscar usuário {user_id}: {e}"
                                    )
                                    descricao += f"   • Usuário indisponível\n"
                        else:
                            descricao += "   • *Nenhum jogador registrado*\n"

                        descricao += "\n"

                descricao += f"**Total de participantes:** {total_registrados}/{total_vagas} jogadores"

                # Desabilitar todos os botões mantendo cores apropriadas
                for item in self.children:
                    if isinstance(item, discord.ui.Button):
                        item.disabled = True
                        # Manter verde para tipos que têm participantes
                        tipo = item.custom_id.split('_')[1]
                        if len(self.votos.get(tipo, [])) > 0:
                            item.style = discord.ButtonStyle.success
                        else:
                            item.style = discord.ButtonStyle.secondary
            else:
                # Embed normal
                embed = discord.Embed(title=f"🎯 {self.enquete_data['titulo']}",
                                      color=discord.Color.blue())

                descricao = f"**📅 Horário:** {self.enquete_data['horario']}\n\n"
                descricao += f"**📜 ** {self.enquete_data['levar']}\n\n"
                descricao += "**Clique nos botões para se registrar:**\n\n"

                for tipo in ordem_tipos:
                    if tipo in self.limites and self.limites[tipo] > 0:
                        emoji = self.emojis[tipo]
                        atual = len(self.votos[tipo])
                        limite = self.limites[tipo]
                        descricao += f"{emoji} **{tipo}**: {atual}/{limite} vagas\n"

                descricao += f"\n**Total Registrados:** {total_registrados}/{total_vagas} jogadores"

            embed.description = descricao

            # Footer diferente para enquete completa
            if enquete_completa:
                embed.set_footer(
                    text=
                    "🎉 Evento finalizada! Todos os slots foram preenchidos.")
            else:
                try:
                    autor = interaction.guild.get_member(
                        self.enquete_data['autor_id'])
                    autor_nome = autor.display_name if autor else "Usuário não encontrado"
                    embed.set_footer(
                        text=
                        f"Evento criada por {autor_nome} • Use /resultado_evento para detalhes"
                    )
                except:
                    embed.set_footer(
                        text="Use /resultado_evento para detalhes")

            # Buscar a mensagem original e editá-la
            channel = interaction.guild.get_channel(
                self.enquete_data['canal_id'])
            message = await channel.fetch_message(
                self.enquete_data['message_id'])
            await message.edit(embed=embed, view=self)

        except Exception as e:
            print(f"Erro ao atualizar botões (followup): {e}")


class EnqueteModal(discord.ui.Modal):

    def __init__(self, cog_instance):
        super().__init__(title="Criar novo evento")
        self.cog_instance = cog_instance

        self.titulo = discord.ui.TextInput(
            label="Eventos",
            placeholder="Ex: Last Livraria : 21:00 - descrição",
            max_length=100,
            required=True)

        self.ek_limite = discord.ui.TextInput(
            label="Quantos TANKER (Elite Knight)",
            placeholder="Número de Elite Knights necessários",
            max_length=2,
            required=True)

        self.ed_limite = discord.ui.TextInput(
            label="Quantos HEALER (Elder Druid)",
            placeholder="Número de Elder Druids necessários",
            max_length=2,
            required=True)

        self.st_limite = discord.ui.TextInput(
            label="Quantos DPS (Shooters/Damage)",
            placeholder="Número de Shooters/Damage necessários",
            max_length=2,
            required=True)

        self.reserva_limite = discord.ui.TextInput(
            label="Quantas Reservas",
            placeholder="Número de jogadores reservas",
            max_length=2,
            required=True)

        self.add_item(self.titulo)
        self.add_item(self.ek_limite)
        self.add_item(self.ed_limite)
        self.add_item(self.st_limite)
        self.add_item(self.reserva_limite)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            limites = {
                'TANKER': int(self.ek_limite.value),
                'HEALER': int(self.ed_limite.value),
                'DPS': int(self.st_limite.value),
                'RESERVA': int(self.reserva_limite.value)
            }

            for tipo, limite in limites.items():
                if limite < 0:
                    await interaction.response.send_message(
                        f"❌ O limite para {tipo} deve ser um número positivo!",
                        ephemeral=True)
                    return

            await self.criar_enquete(interaction, limites)

        except ValueError:
            await interaction.response.send_message(
                "❌ Por favor, digite apenas números válidos para os limites!",
                ephemeral=True)

    async def criar_enquete(self, interaction, limites):
        try:
            # Limpar memória de enquetes antigas
            self.cog_instance.active_views.clear()

            # Gerar ID único para o evento
            event_id = str(uuid.uuid4())

            # Criar dados da enquete com horário de Brasília
            brasilia_tz = pytz.timezone('America/Sao_Paulo')
            now_brasilia = datetime.now(brasilia_tz)

            enquete_data = {
                'event_id':
                event_id,
                'titulo':
                self.titulo.value.split(':')[0].strip(),
                'levar':
                self.titulo.value.split('-')[-1].strip()
                if '-' in self.titulo.value else "Não especificado",
                'horario':
                self.titulo.value.split(':')[1].split('-')[0].strip()
                if ':' in self.titulo.value else "Não especificado",
                'limites':
                limites,
                'data_criacao':
                now_brasilia.isoformat(),
                'data_criacao_brasilia':
                now_brasilia.strftime("%d/%m/%Y às %H:%M:%S"),
                'autor_id':
                interaction.user.id,
                'autor_nome':
                interaction.user.display_name,
                'canal_id':
                interaction.channel.id,
                'ativa':
                True,
                'tipo':
                'enquete'
            }

            # Criar embed
            embed = discord.Embed(title=f"🎯 {enquete_data['titulo']}",
                                  color=discord.Color.blue())

            descricao = f"**📅 Horário:** {enquete_data['horario']}\n\n"
            descricao += f"**📜 ** {enquete_data['levar']}\n\n"
            descricao += "**Clique nos botões para se registrar:**\n\n"

            emojis = {
                'TANKER': '🛡️',
                'HEALER': '🚑',
                'DPS': '⚔️',
                'RESERVA': '🔄'
            }
            ordem_tipos = ['TANKER', 'HEALER', 'DPS', 'RESERVA']

            total_vagas = 0
            for tipo in ordem_tipos:
                if limites[tipo] > 0:
                    emoji = emojis[tipo]
                    descricao += f"{emoji} **{tipo}**: 0/{limites[tipo]} vagas\n"
                    total_vagas += limites[tipo]

            descricao += f"\n**Total de vagas:** {total_vagas} jogadores"
            descricao += f"\n@everyone"
            embed.description = descricao
            embed.set_footer(
                text=
                f"Enquete criada por {interaction.user.display_name} • Use /resultado_evento para detalhes"
            )

            # Criar view com botões
            view = EnqueteView(interaction.client, enquete_data, limites)

            # Enviar no canal
            mensagem = await interaction.channel.send(embed=embed, view=view)

            # Atualizar dados com ID da mensagem
            enquete_data['message_id'] = mensagem.id

            # Salvar no JSON
            storage = EventStorage()
            storage.save_event(enquete_data)

            # Salvar view na memória
            self.cog_instance.active_views[mensagem.id] = view
            view.enquete_data = enquete_data

            await interaction.response.send_message(
                "✅ Evento criada com sucesso!", ephemeral=True)

        except Exception as e:
            print(f"Erro ao criar enquete: {e}")
            await interaction.response.send_message(
                "❌ Erro ao criar evento. Tente novamente!", ephemeral=True)


class EventSelectView(discord.ui.View):

    def __init__(self, events_data, interaction_user):
        super().__init__(timeout=60)
        self.events_data = events_data
        self.interaction_user = interaction_user

        # Criar dropdown com os eventos
        options = []
        for i, event in enumerate(events_data):
            # Formatar data para o label
            try:
                # Verificar se já temos data formatada do Brasil
                if 'data_criacao_brasilia' in event:
                    data_formatada = event['data_criacao_brasilia'].split(
                        ' às ')[1].replace(' (Brasília)', '')
                    data_formatada = event['data_criacao_brasilia'].split(
                        ' às ')[0] + " " + data_formatada[:5]
                else:
                    # Fallback para datas antigas
                    dt = datetime.fromisoformat(event['data_criacao'].replace(
                        'Z', '+00:00'))
                    brasilia_tz = pytz.timezone('America/Sao_Paulo')
                    dt_brasilia = dt.astimezone(brasilia_tz)
                    data_formatada = dt_brasilia.strftime("%d/%m %H:%M")
            except:
                data_formatada = "Data inválida"

            # Contar participantes
            total_participantes = 0
            if 'participantes' in event:
                for tipo_participantes in event['participantes'].values():
                    total_participantes += len(tipo_participantes)

            options.append(
                discord.SelectOption(
                    label=f"{event['titulo']} - {data_formatada}",
                    description=
                    f"Participantes: {total_participantes} | Por: {event.get('autor_nome', 'Desconhecido')}",
                    value=str(i)))

        if options:
            select = discord.ui.Select(
                placeholder="Selecione um evento para ver detalhes...",
                options=options)
            select.callback = self.select_callback
            self.add_item(select)

    async def select_callback(self, interaction):
        try:
            if interaction.user.id != self.interaction_user.id:
                await interaction.response.send_message(
                    "❌ Apenas quem executou o comando pode usar esta seleção!",
                    ephemeral=True)
                return

            # Pegar o evento selecionado
            event_index = int(interaction.data['values'][0])
            event = self.events_data[event_index]

            # Criar embed detalhado
            embed = discord.Embed(
                title=f"📊 Detalhes do Evento: {event['titulo']}",
                color=discord.Color.green())

            # Informações básicas
            try:
                # Verificar se já temos data formatada do Brasil
                if 'data_criacao_brasilia' in event:
                    data_formatada = event['data_criacao_brasilia']
                else:
                    # Fallback para datas antigas
                    dt = datetime.fromisoformat(event['data_criacao'].replace(
                        'Z', '+00:00'))
                    brasilia_tz = pytz.timezone('America/Sao_Paulo')
                    dt_brasilia = dt.astimezone(brasilia_tz)
                    data_formatada = dt_brasilia.strftime(
                        "%d/%m/%Y às %H:%M (Brasília)")
            except:
                data_formatada = "Data inválida"

            descricao = f"**📅 Horário:** {event.get('horario', 'Não especificado')}\n"
            descricao += f"**📜 {event.get('levar', 'Não especificado')}**\n"
            descricao += f"**👤 Criado por:** {event.get('autor_nome', 'Desconhecido')}\n"
            descricao += f"**🕒 Data de criação:** {data_formatada}\n\n"

            # Participantes
            if 'participantes' in event and event['participantes']:
                descricao += "**👥 PARTICIPANTES:**\n\n"

                emojis = {
                    'TANKER': '🛡️',
                    'HEALER': '🚑',
                    'DPS': '⚔️',
                    'RESERVA': '🔄'
                }

                total_participantes = 0
                for tipo, participantes in event['participantes'].items():
                    if participantes:
                        emoji = emojis.get(tipo, '❓')
                        limite = event.get('limites', {}).get(tipo, 0)
                        descricao += f"{emoji} **{tipo}** ({len(participantes)}/{limite}):\n"

                        for participante in participantes:
                            user_id = participante.get('user_id')
                            nome_display = 'Nome não disponível'

                            try:
                                # PRIORIDADE 1: Nickname atual do servidor (display_name inclui nickname se houver)
                                if user_id:
                                    guild = interaction.guild
                                    member = guild.get_member(user_id)
                                    if member:
                                        # PRIORIDADE 1: Nickname específico do servidor
                                        if member.nick:
                                            nome_display = member.nick
                                        # PRIORIDADE 2: Nome global do Discord
                                        else:
                                            nome_display = member.global_name or member.name
                                    else:
                                        # PRIORIDADE 2: Nome salvo no evento (nickname que tinha na época)
                                        nome_salvo = participante.get(
                                            'nome_servidor'
                                        ) or participante.get('nome')
                                        if nome_salvo:
                                            nome_display = f"{nome_salvo} (não está mais no servidor)"
                                        else:
                                            nome_display = "Usuário saiu do servidor"
                                else:
                                    # Fallback para eventos antigos sem user_id
                                    nome_display = participante.get(
                                        'nome_servidor') or participante.get(
                                            'nome', 'Nome não disponível')
                            except Exception as e:
                                print(
                                    f"Erro ao buscar nome do usuário {user_id}: {e}"
                                )
                                nome_display = participante.get(
                                    'nome_servidor') or participante.get(
                                        'nome', 'Nome não disponível')

                            descricao += f"   • {nome_display}\n"

                        descricao += "\n"
                        total_participantes += len(participantes)

                descricao += f"**Total de participantes:** {total_participantes}"
            else:
                descricao += "**👥 PARTICIPANTES:** Nenhum participante registrado"

            embed.description = descricao
            embed.set_footer(
                text=f"ID do Evento: {event.get('event_id', 'N/A')}")

            await interaction.response.edit_message(embed=embed, view=None)

        except Exception as e:
            print(f"Erro ao mostrar detalhes do evento: {e}")
            await interaction.response.send_message(
                "❌ Erro ao carregar detalhes do evento.", ephemeral=True)


class EventDeleteSelect(discord.ui.Select):
    """Select menu para escolher eventos para deletar"""

    def __init__(self, eventos):
        self.eventos = eventos

        options = []
        for evento in eventos[:25]:  # Discord limita a 25 opções
            # Truncar título se for muito longo
            titulo = evento.get('titulo', 'Sem título')
            if len(titulo) > 50:
                titulo = titulo[:47] + "..."

            # Formatar data
            if 'data_criacao_brasilia' in evento:
                try:
                    data_formatada = evento['data_criacao_brasilia'].split(
                        ' às ')[1].replace(' (Brasília)', '')
                    data_formatada = evento['data_criacao_brasilia'].split(
                        ' às ')[0] + " " + data_formatada[:5]
                except:
                    data_formatada = 'Data inválida'
            elif evento.get('data_criacao'):
                try:
                    dt = datetime.fromisoformat(evento['data_criacao'].replace(
                        'Z', '+00:00'))
                    brasilia_tz = pytz.timezone('America/Sao_Paulo')
                    dt_brasilia = dt.astimezone(brasilia_tz)
                    data_formatada = dt_brasilia.strftime('%d/%m %H:%M')
                except:
                    data_formatada = 'Data inválida'
            else:
                data_formatada = 'Sem data'

            options.append(
                discord.SelectOption(
                    label=f"{titulo}",
                    description=
                    f"Criado em {data_formatada} por {evento.get('autor_nome', 'Desconhecido')}",
                    value=evento.get('event_id', '')))

        super().__init__(
            placeholder="Selecione os eventos que deseja deletar...",
            min_values=1,
            max_values=len(options),
            options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_ids = self.values
        selected_eventos = [
            e for e in self.eventos if e.get('event_id') in selected_ids
        ]

        # Criar view de confirmação
        view = DeleteConfirmView(selected_eventos, selected_ids)

        embed = discord.Embed(
            title="⚠️ Confirmar Deleção",
            description=
            f"**Você selecionou {len(selected_eventos)} evento(s) para deletar:**\n\n",
            color=discord.Color.red())

        for evento in selected_eventos:
            titulo = evento.get('titulo', 'Sem título')
            if 'data_criacao_brasilia' in evento:
                data_formatada = evento['data_criacao_brasilia']
            elif evento.get('data_criacao'):
                try:
                    dt = datetime.fromisoformat(evento['data_criacao'].replace(
                        'Z', '+00:00'))
                    brasilia_tz = pytz.timezone('America/Sao_Paulo')
                    dt_brasilia = dt.astimezone(brasilia_tz)
                    data_formatada = dt_brasilia.strftime(
                        '%d/%m/%Y às %H:%M (Brasília)')
                except:
                    data_formatada = 'Data inválida'
            else:
                data_formatada = 'Sem data'

            embed.add_field(
                name=f"📅 {titulo}",
                value=
                f"Criado em {data_formatada}\nPor: {evento.get('autor_nome', 'Desconhecido')}",
                inline=True)

        embed.add_field(
            name="⚠️ ATENÇÃO",
            value=
            "**Esta ação não pode ser desfeita!**\nTodos os dados dos eventos selecionados serão permanentemente removidos.",
            inline=False)

        await interaction.response.edit_message(embed=embed, view=view)


class DeleteConfirmView(discord.ui.View):
    """View para confirmar a deleção dos eventos"""

    def __init__(self, eventos, event_ids):
        super().__init__(timeout=300)
        self.eventos = eventos
        self.event_ids = event_ids

    @discord.ui.button(label="🗑️ Confirmar Deleção",
                       style=discord.ButtonStyle.danger)
    async def confirm_delete(self, interaction: discord.Interaction,
                             button: discord.ui.Button):
        storage = EventStorage()

        if storage.delete_events(self.event_ids):
            embed = discord.Embed(
                title="✅ Eventos Deletados",
                description=
                f"**{len(self.eventos)} evento(s) foram deletados com sucesso!**",
                color=discord.Color.green())

            deletados_list = []
            for evento in self.eventos:
                titulo = evento.get('titulo', 'Sem título')
                deletados_list.append(f"• {titulo}")

            if deletados_list:
                embed.add_field(name="Eventos removidos:",
                                value="\n".join(deletados_list),
                                inline=False)

            await interaction.response.edit_message(embed=embed, view=None)
        else:
            embed = discord.Embed(
                title="❌ Erro na Deleção",
                description=
                "Ocorreu um erro ao deletar os eventos. Tente novamente.",
                color=discord.Color.red())
            await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="❌ Cancelar", style=discord.ButtonStyle.secondary)
    async def cancel_delete(self, interaction: discord.Interaction,
                            button: discord.ui.Button):
        embed = discord.Embed(title="🚫 Deleção Cancelada",
                              description="Nenhum evento foi removido.",
                              color=discord.Color.blue())
        await interaction.response.edit_message(embed=embed, view=None)


class EventDeleteView(discord.ui.View):
    """View principal para seleção de eventos para deletar"""

    def __init__(self, eventos):
        super().__init__(timeout=300)
        self.add_item(EventDeleteSelect(eventos))


class Enquete(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.active_views = {}  # {message_id: EnqueteView}
        self.storage = EventStorage()

    @app_commands.command(name="criar_evento_boss",
                          description="Criar uma nova enquete Eventos")
    async def enquete_slash(self, interaction: discord.Interaction):
        cargo_permitido = discord.utils.get(
            interaction.guild.roles,
            name="Puxadores")  # Nome do cargo permitido

        if cargo_permitido not in interaction.user.roles:
            await interaction.response.send_message(
                "❌ Você não tem permissão para usar este comando!",
                ephemeral=True)
            return

        # Limpar memória antes de criar nova enquete
        self.active_views.clear()
        modal = EnqueteModal(self)
        await interaction.response.send_modal(modal)

    @app_commands.command(
        name="deletar_eventos",
        description="Deletar eventos salvos do armazenamento")
    async def deletar_eventos_slash(self, interaction: discord.Interaction):
        # Verificar permissões - só quem pode criar eventos pode deletar
        cargo_permitido = discord.utils.get(interaction.guild.roles,
                                            name="Puxadores")

        if cargo_permitido not in interaction.user.roles:
            await interaction.response.send_message(
                "❌ Você não tem permissão para usar este comando!",
                ephemeral=True)
            return

        # Buscar todos os eventos
        todos_eventos = self.storage.get_all_events()

        if not todos_eventos:
            embed = discord.Embed(
                title="📋 Nenhum Evento Encontrado",
                description="Não há eventos salvos para deletar.",
                color=discord.Color.blue())
            await interaction.response.send_message(embed=embed,
                                                    ephemeral=True)
            return

        # Ordenar eventos do mais recente para o mais antigo
        todos_eventos.sort(key=lambda x: x.get('data_criacao', ''),
                           reverse=True)

        # Limitar a 25 eventos (limite do Discord)
        eventos_para_mostrar = todos_eventos[:25]

        embed = discord.Embed(
            title="🗑️ Deletar Eventos",
            description=
            f"**{len(todos_eventos)} evento(s) encontrado(s)** no armazenamento.\n\n"
            f"🔹 **Instruções:**\n"
            f"• Selecione um ou mais eventos para deletar\n"
            f"• Você pode escolher até {len(eventos_para_mostrar)} eventos por vez\n"
            f"• A ação será irreversível após confirmação\n\n"
            f"📋 **Eventos disponíveis:**",
            color=discord.Color.orange())

        if len(todos_eventos) > 25:
            embed.add_field(
                name="⚠️ Limite de Exibição",
                value=
                f"Mostrando apenas os 25 eventos mais recentes.\nTotal no sistema: {len(todos_eventos)}",
                inline=False)

        view = EventDeleteView(eventos_para_mostrar)
        await interaction.response.send_message(embed=embed,
                                                view=view,
                                                ephemeral=True)

    @app_commands.command(name="resultado_evento",
                          description="Ver resultados dos últimos eventos")
    async def resultado_slash(self, interaction: discord.Interaction):
        cargo_permitido = discord.utils.get(interaction.guild.roles,
                                            name="Puxadores")

        if cargo_permitido not in interaction.user.roles:
            await interaction.response.send_message(
                "❌ Você não tem permissão para usar este comando!",
                ephemeral=True)
            return

        # Buscar os últimos 5 eventos
        recent_events = self.storage.get_recent_events(5)

        if not recent_events:
            await interaction.response.send_message(
                "❌ Nenhum evento encontrado!", ephemeral=True)
            return

        # Criar embed inicial
        embed = discord.Embed(
            title="📋 Últimos Eventos Criados",
            description=
            "Selecione um evento abaixo para ver os detalhes e participantes:",
            color=discord.Color.blue())

        # Adicionar lista resumida dos eventos
        lista_eventos = ""
        for i, event in enumerate(recent_events, 1):
            try:
                dt = datetime.fromisoformat(event['data_criacao'])
                data_formatada = dt.strftime("%d/%m %H:%M")
            except:
                data_formatada = "Data inválida"

            # Contar participantes
            total_participantes = 0
            if 'participantes' in event:
                for tipo_participantes in event['participantes'].values():
                    total_participantes += len(tipo_participantes)

            lista_eventos += f"**{i}.** {event['titulo']} - {data_formatada}\n"
            lista_eventos += f"    Participantes: {total_participantes} | Criado por: {event.get('autor_nome', 'Desconhecido')}\n\n"

        embed.add_field(name="📅 Eventos Recentes:",
                        value=lista_eventos,
                        inline=False)

        # Criar view com seleção
        view = EventSelectView(recent_events, interaction.user)

        await interaction.response.send_message(embed=embed,
                                                view=view,
                                                ephemeral=True)

    @app_commands.command(name="limpar_evento",
                          description="Limpar enquetes da memória")
    async def limpar_slash(self, interaction: discord.Interaction):
        cargo_permitido = discord.utils.get(interaction.guild.roles,
                                            name="Puxadores")

        if cargo_permitido not in interaction.user.roles:
            await interaction.response.send_message(
                "❌ Você não tem permissão para usar este comando!",
                ephemeral=True)
            return

        self.active_views.clear()
        await interaction.response.send_message(
            "✅ Memória de enquetes limpa com sucesso!", ephemeral=True)

    @app_commands.command(
        name="sync_comandos",
        description="[ADMIN] Forçar sincronização dos comandos slash")
    async def sync_comandos(self, interaction: discord.Interaction):
        # Verificar se é administrador
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ Apenas administradores podem usar este comando!",
                ephemeral=True)
            return

        try:
            await interaction.response.defer(ephemeral=True)

            # Sincronizar comandos
            synced = await self.bot.tree.sync()

            await interaction.followup.send(
                f"✅ **Comandos sincronizados com sucesso!**\n\n"
                f"📊 **{len(synced)} comandos** foram sincronizados com o Discord.\n"
                f"🔄 Os comandos devem aparecer em alguns segundos.\n\n"
                f"💡 **Dica:** Se ainda não aparecerem, tente:\n"
                f"• Fechar e reabrir o Discord\n"
                f"• Sair e entrar no servidor novamente",
                ephemeral=True)

        except Exception as e:
            await interaction.followup.send(
                f"❌ **Erro ao sincronizar comandos:**\n```{str(e)}```",
                ephemeral=True)


async def setup(bot):
    await bot.add_cog(Enquete(bot))