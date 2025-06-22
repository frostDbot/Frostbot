import discord
from discord.ext import commands
from discord import app_commands
import logging
import re
from verification_storage import VerificationStorage

# Configurar logging específico para verificação
logger = logging.getLogger('verificacao')
handler = logging.FileHandler('verificacao.log', encoding='utf-8')
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


class NicknameModal(discord.ui.Modal):
    """Modal para edição de nickname"""

    def __init__(self):
        super().__init__(title="📝 Definir Nickname do Servidor")

        self.nickname_input = discord.ui.TextInput(
            label="Nickname para este servidor:",
            placeholder=
            "Exemplo: [EK 900+] Noctiis, [MS 500+] Player, [RP 300+] Nome",
            max_length=32,
            required=True,
            style=discord.TextStyle.short)
        self.add_item(self.nickname_input)

    async def on_submit(self, interaction: discord.Interaction):
        """Processar submissão do nickname"""
        try:
            new_nickname = self.nickname_input.value.strip()

            # Validações básicas
            if len(new_nickname) < 2:
                await interaction.response.send_message(
                    "❌ O nickname deve ter pelo menos 2 caracteres!",
                    ephemeral=True)
                return

            # Verificar se contém caracteres proibidos
            if any(char in new_nickname for char in ['@', '#', ':', '```']):
                await interaction.response.send_message(
                    "❌ O nickname não pode conter os caracteres: @, #, :, ```",
                    ephemeral=True)
                return

            # Tentar definir o nickname
            try:
                await interaction.user.edit(
                    nick=new_nickname, reason="Verificação de novo membro")

                # Log da ação
                logger.info(
                    f"Nickname definido - Usuário: {interaction.user.id} ({interaction.user.name}) - Novo nick: {new_nickname}"
                )

                # Atualizar dados da verificação com nickname
                storage = VerificationStorage()
                existing_data = storage.get_verification_by_user(
                    interaction.user.id)
                if existing_data:
                    existing_data["nick_atual_servidor"] = new_nickname
                    existing_data["status"] = "nickname_definido"
                    storage.save_verification(existing_data)
                else:
                    # Criar novo registro se não existir
                    user_data = {
                        "user_id":
                        interaction.user.id,
                        "nick_discord":
                        interaction.user.name,
                        "nome_global":
                        interaction.user.global_name or interaction.user.name,
                        "nick_atual_servidor":
                        new_nickname,
                        "vocacao":
                        None,
                        "status":
                        "nickname_definido"
                    }
                    storage.save_verification(user_data)

                # Criar embed de sucesso
                embed = discord.Embed(
                    title="✅ Nickname Definido!",
                    description=
                    f"Seu nickname foi alterado para: **{new_nickname}**",
                    color=discord.Color.green())

                # Criar view para próxima etapa
                view = VocacaoSelectView()

                embed.add_field(
                    name="🎯 Próximo Passo:",
                    value=
                    "Agora você receberá o cargo de **Convidado** e poderá escolher sua vocação!",
                    inline=False)

                await interaction.response.send_message(embed=embed,
                                                        view=view,
                                                        ephemeral=True)

            except discord.Forbidden:
                await interaction.response.send_message(
                    "❌ Não tenho permissão para alterar seu nickname. Contate um administrador.",
                    ephemeral=True)
                logger.error(
                    f"Sem permissão para alterar nickname - Usuário: {interaction.user.id}"
                )

            except discord.HTTPException as e:
                await interaction.response.send_message(
                    "❌ Erro ao definir nickname. Tente novamente ou contate um administrador.",
                    ephemeral=True)
                logger.error(
                    f"Erro HTTP ao alterar nickname - Usuário: {interaction.user.id} - Erro: {e}"
                )

        except Exception as e:
            logger.error(
                f"Erro inesperado no modal de nickname - Usuário: {interaction.user.id} - Erro: {e}"
            )
            await interaction.response.send_message(
                "❌ Ocorreu um erro inesperado. Tente novamente.",
                ephemeral=True)


class VocacaoSelectView(discord.ui.View):
    """View para seleção de vocação"""

    def __init__(self):
        super().__init__(timeout=300)
        self.setup_buttons()

    def setup_buttons(self):
        """Configurar botões de vocação"""

        # Mapear vocações com emojis
        vocacoes = {
            "EK": {
                "emoji": "🛡️",
                "name": "Elite Knight",
                "style": discord.ButtonStyle.primary
            },
            "MS": {
                "emoji": "🔮",
                "name": "Master Sorcerer",
                "style": discord.ButtonStyle.secondary
            },
            "RP": {
                "emoji": "🏹",
                "name": "Royal Paladin",
                "style": discord.ButtonStyle.success
            },
            "ED": {
                "emoji": "🌟",
                "name": "Elder Druid",
                "style": discord.ButtonStyle.danger
            },
            "MK": {
                "emoji": "👊",
                "name": "Monk",
                "style": discord.ButtonStyle.grey
            }
        }

        for voc_code, voc_data in vocacoes.items():
            button = discord.ui.Button(
                label=f"{voc_data['name']} ({voc_code})",
                emoji=voc_data['emoji'],
                style=voc_data['style'],
                custom_id=f"voc_{voc_code}")
            button.callback = self.create_vocacao_callback(voc_code)
            self.add_item(button)

        # Removido botão de pular - vocação agora é obrigatória

    def create_vocacao_callback(self, vocacao_code):
        """Criar callback específico para cada vocação"""

        async def vocacao_callback(interaction: discord.Interaction):
            await self.handle_vocacao_selection(interaction, vocacao_code)

        return vocacao_callback

    async def handle_vocacao_selection(self, interaction: discord.Interaction,
                                       vocacao_code: str):
        """Processar seleção de vocação"""
        try:
            guild = interaction.guild
            user = interaction.user

            # Buscar cargos
            cargo_convidado = discord.utils.get(guild.roles, name="Convidado")
            cargo_vocacao = discord.utils.get(guild.roles, name=vocacao_code)

            # Verificar se os cargos existem
            cargos_para_adicionar = []
            mensagens_erro = []

            if cargo_convidado:
                cargos_para_adicionar.append(cargo_convidado)
            else:
                mensagens_erro.append("Cargo 'Convidado' não encontrado")
                logger.error(
                    f"Cargo 'Convidado' não encontrado no servidor {guild.name}"
                )

            if cargo_vocacao:
                cargos_para_adicionar.append(cargo_vocacao)
            else:
                mensagens_erro.append(f"Cargo '{vocacao_code}' não encontrado")
                logger.error(
                    f"Cargo '{vocacao_code}' não encontrado no servidor {guild.name}"
                )

            # Se houver erros críticos, informar
            if not cargo_convidado:
                await interaction.response.send_message(
                    "❌ Erro de configuração: Cargo 'Convidado' não foi encontrado. Contate um administrador.",
                    ephemeral=True)
                return

            # Tentar adicionar os cargos
            cargos_adicionados = []

            try:
                for cargo in cargos_para_adicionar:
                    if cargo not in user.roles:
                        await user.add_roles(
                            cargo,
                            reason="Verificação de novo membro concluída")
                        cargos_adicionados.append(cargo.name)
                        logger.info(
                            f"Cargo adicionado - Usuário: {user.id} ({user.name}) - Cargo: {cargo.name}"
                        )

                # Criar embed de conclusão
                embed = discord.Embed(title="🎉 Verificação Concluída!",
                                      description="Bem-vindo(a) ao servidor!",
                                      color=discord.Color.gold())

                if cargos_adicionados:
                    embed.add_field(name="✅ Cargos Recebidos:",
                                    value="\n".join([
                                        f"• {cargo}"
                                        for cargo in cargos_adicionados
                                    ]),
                                    inline=False)

                if cargo_vocacao:
                    vocacao_info = {
                        "EK": "🛡️ Elite Knight - Tanque e proteção",
                        "MS": "🔮 Master Sorcerer - Dano mágico",
                        "ED": "🌟 Elder Druid - Suporte e cura",
                        "RP": "🏹 Royal Paladin - Dano à distância",
                        "MK": "👊 Monk - Combate corpo a corpo"
                    }

                    embed.add_field(name="🎯 Sua Vocação:",
                                    value=vocacao_info.get(
                                        vocacao_code, f"{vocacao_code}"),
                                    inline=False)

                embed.add_field(
                    name="📋 Próximos Passos:",
                    value=
                    "• Explore os canais do servidor\n• Participe das conversas\n• Divirta-se!",
                    inline=False)

                embed.set_footer(
                    text="Agora você tem acesso completo ao servidor!")

                await interaction.response.edit_message(embed=embed, view=None)

                # Log de conclusão
                logger.info(
                    f"Verificação concluída - Usuário: {user.id} ({user.name}) - Vocação: {vocacao_code}"
                )

            except discord.Forbidden:
                await interaction.response.send_message(
                    "❌ Não tenho permissão para adicionar cargos. Contate um administrador.",
                    ephemeral=True)
                logger.error(
                    f"Sem permissão para adicionar cargos - Usuário: {user.id}"
                )

            except discord.HTTPException as e:
                await interaction.response.send_message(
                    "❌ Erro ao adicionar cargos. Contate um administrador.",
                    ephemeral=True)
                logger.error(
                    f"Erro HTTP ao adicionar cargos - Usuário: {user.id} - Erro: {e}"
                )

        except Exception as e:
            logger.error(
                f"Erro inesperado na seleção de vocação - Usuário: {interaction.user.id} - Erro: {e}"
            )
            await interaction.response.send_message(
                "❌ Ocorreu um erro inesperado. Tente novamente ou contate um administrador.",
                ephemeral=True)

    # Callback de pular removido - vocação agora é obrigatória

    async def handle_vocacao_selection(self, interaction: discord.Interaction,
                                       vocacao_code: str):
        """Processar seleção ou pulo de vocação"""
        try:
            guild = interaction.guild
            user = interaction.user

            # Buscar cargo Convidado (obrigatório)
            cargo_convidado = discord.utils.get(guild.roles, name="Convidado")

            if not cargo_convidado:
                await interaction.response.send_message(
                    "❌ Erro de configuração: Cargo 'Convidado' não foi encontrado. Contate um administrador.",
                    ephemeral=True)
                logger.error(
                    f"Cargo 'Convidado' não encontrado no servidor {guild.name}"
                )
                return

            # Adicionar cargo Convidado
            cargos_adicionados = []

            try:
                if cargo_convidado not in user.roles:
                    await user.add_roles(
                        cargo_convidado,
                        reason="Verificação de novo membro concluída")
                    cargos_adicionados.append("Convidado")
                    logger.info(
                        f"Cargo Convidado adicionado - Usuário: {user.id} ({user.name})"
                    )

                # Adicionar cargo de vocação (agora obrigatório)
                cargo_vocacao = discord.utils.get(guild.roles,
                                                  name=vocacao_code)
                if cargo_vocacao and cargo_vocacao not in user.roles:
                    await user.add_roles(
                        cargo_vocacao,
                        reason=
                        "Verificação de novo membro - vocação selecionada")
                    cargos_adicionados.append(vocacao_code)
                    logger.info(
                        f"Cargo {vocacao_code} adicionado - Usuário: {user.id} ({user.name})"
                    )

                # Criar embed de conclusão
                embed = discord.Embed(title="🎉 Verificação Concluída!",
                                      description="Bem-vindo(a) ao servidor!",
                                      color=discord.Color.gold())

                if cargos_adicionados:
                    embed.add_field(name="✅ Cargos Recebidos:",
                                    value="\n".join([
                                        f"• {cargo}"
                                        for cargo in cargos_adicionados
                                    ]),
                                    inline=False)

                vocacao_info = {
                    "EK": "🛡️ Elite Knight - Tanque e proteção",
                    "MS": "🔮 Master Sorcerer - Dano mágico",
                    "ED": "🌟 Elder Druid - Suporte e cura",
                    "RP": "🏹 Royal Paladin - Dano à distância",
                    "MK": "👊 Monk - Combate corpo a corpo"
                }

                embed.add_field(name="🎯 Sua Vocação:",
                                value=vocacao_info.get(vocacao_code,
                                                       f"{vocacao_code}"),
                                inline=False)

                embed.add_field(
                    name="📋 Próximos Passos:",
                    value=
                    "• Explore os canais do servidor\n• Participe das conversas\n• Divirta-se!",
                    inline=False)

                embed.set_footer(
                    text="Agora você tem acesso completo ao servidor!")

                await interaction.response.edit_message(embed=embed, view=None)

                # Salvar dados finais da verificação
                storage = VerificationStorage()
                existing_data = storage.get_verification_by_user(user.id)
                if existing_data:
                    existing_data["vocacao"] = vocacao_code
                    existing_data["status"] = "verificacao_concluida"
                    storage.save_verification(existing_data)
                else:
                    # Criar novo registro se não existir
                    user_data = {
                        "user_id": user.id,
                        "nick_discord": user.name,
                        "nome_global": user.global_name or user.name,
                        "nick_atual_servidor": user.nick,
                        "vocacao": vocacao_code,
                        "status": "verificacao_concluida"
                    }
                    storage.save_verification(user_data)

                # Log de conclusão
                logger.info(
                    f"Verificação concluída com vocação {vocacao_code} - Usuário: {user.id} ({user.name})"
                )

            except discord.Forbidden:
                await interaction.response.send_message(
                    "❌ Não tenho permissão para adicionar cargos. Contate um administrador.",
                    ephemeral=True)
                logger.error(
                    f"Sem permissão para adicionar cargos - Usuário: {user.id}"
                )

            except discord.HTTPException as e:
                await interaction.response.send_message(
                    "❌ Erro ao adicionar cargos. Contate um administrador.",
                    ephemeral=True)
                logger.error(
                    f"Erro HTTP ao adicionar cargos - Usuário: {user.id} - Erro: {e}"
                )

        except Exception as e:
            logger.error(
                f"Erro inesperado ao processar verificação - Usuário: {interaction.user.id} - Erro: {e}"
            )
            await interaction.response.send_message(
                "❌ Ocorreu um erro inesperado. Tente novamente ou contate um administrador.",
                ephemeral=True)


class VerificationPanelView(discord.ui.View):
    """View principal do painel de verificação"""

    def __init__(self):
        super().__init__(timeout=None)  # Persistent view

    @discord.ui.button(label="🚀 Começar Verificação",
                       style=discord.ButtonStyle.primary,
                       emoji="🚀",
                       custom_id="start_verification")
    async def start_verification(self, interaction: discord.Interaction,
                                 button: discord.ui.Button):
        """Iniciar processo de verificação"""
        try:
            # Verificar se o usuário já tem o cargo de Convidado
            cargo_convidado = discord.utils.get(interaction.guild.roles,
                                                name="Convidado")

            if cargo_convidado and cargo_convidado in interaction.user.roles:
                embed = discord.Embed(
                    title="ℹ️ Você já está verificado!",
                    description=
                    "Você já possui o cargo de Convidado e tem acesso ao servidor.",
                    color=discord.Color.blue())
                await interaction.response.send_message(embed=embed,
                                                        ephemeral=True)
                return

            # Criar embed de boas-vindas
            embed = discord.Embed(
                title="👋 Bem-vindo(a) ao servidor!",
                description=
                "Para acessar todos os canais, você precisa completar a verificação:",
                color=discord.Color.green())

            embed.add_field(
                name="📝 **1. Definir Nickname (Obrigatório)**",
                value=
                "Primeiro, vamos definir seu nickname para este servidor.\n"
                "**Sugestão:** `[VOCAÇÃO LEVEL+] SeuNome`\n"
                "**Exemplos:** `[EK 900+] Noctiis`, `[MS 500+] Player`",
                inline=False)

            embed.add_field(
                name="🎯 **2. Cargo Convidado (Automático)**",
                value="Você receberá automaticamente o cargo de **Convidado**",
                inline=False)

            embed.add_field(name="⚔️ **3. Escolher Vocação (Obrigatório)**",
                            value="🛡️ **EK** - Elite Knight\n"
                            "🔮 **MS** - Master Sorcerer\n"
                            "🏹 **RP** - Royal Paladin\n"
                            "🌟 **ED** - Elder Druid\n"
                            "👊 **MK** - Monk",
                            inline=False)

            embed.set_footer(text="Clique no botão abaixo para começar!")

            # Botão para abrir modal de nickname
            view = discord.ui.View()
            nickname_button = discord.ui.Button(
                label="📝 Definir Nickname",
                style=discord.ButtonStyle.success,
                emoji="📝")
            nickname_button.callback = self.open_nickname_modal
            view.add_item(nickname_button)

            await interaction.response.send_message(embed=embed,
                                                    view=view,
                                                    ephemeral=True)

            # Log do início da verificação
            logger.info(
                f"Verificação iniciada - Usuário: {interaction.user.id} ({interaction.user.name})"
            )

            # Salvar dados iniciais da verificação
            storage = VerificationStorage()
            user_data = {
                "user_id": interaction.user.id,
                "nick_discord": interaction.user.name,
                "nome_global": interaction.user.global_name
                or interaction.user.name,
                "nick_atual_servidor":
                None,  # Será preenchido quando definir nickname
                "vocacao": None,  # Será preenchido quando escolher vocação
                "status": "verificacao_iniciada"
            }
            storage.save_verification(user_data)

        except Exception as e:
            logger.error(
                f"Erro ao iniciar verificação - Usuário: {interaction.user.id} - Erro: {e}"
            )
            await interaction.response.send_message(
                "❌ Ocorreu um erro ao iniciar a verificação. Tente novamente.",
                ephemeral=True)

    async def open_nickname_modal(self, interaction: discord.Interaction):
        """Abrir modal para definir nickname"""
        modal = NicknameModal()
        await interaction.response.send_modal(modal)


class Verificacao(commands.Cog):
    """Cog para sistema de verificação de novos membros"""

    def __init__(self, bot):
        self.bot = bot
        self.setup_persistent_views()

    def setup_persistent_views(self):
        """Configurar views persistentes"""
        self.bot.add_view(VerificationPanelView())
        logger.info("Views persistentes de verificação configuradas")

    @app_commands.command(
        name="criar_painel_verificacao",
        description="[ADMIN] Criar painel de verificação para novos membros")
    @app_commands.describe(
        canal="Canal onde criar o painel (padrão: canal atual)")
    async def criar_painel_verificacao(self,
                                       interaction: discord.Interaction,
                                       canal: discord.TextChannel = None):
        """Comando para criar painel de verificação"""

        # Verificar permissões
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ Apenas administradores podem usar este comando!",
                ephemeral=True)
            return

        # Definir canal
        target_channel = canal or interaction.channel

        try:
            # Criar embed do painel
            embed = discord.Embed(
                title="🔐 Verificação de Novos Membros",
                description="**Bem-vindo(a) ao nosso servidor!**\n\n"
                "Para acessar todos os canais e participar da comunidade, "
                "você precisa completar um processo rápido de verificação.\n\n"
                "**O que você precisa fazer:**",
                color=discord.Color.blue())

            embed.add_field(name="1️⃣ Definir Nickname",
                            value="Configure seu nickname para este servidor\n"
                            "**Formato sugerido:** `[VOCAÇÃO LEVEL+] Nome`",
                            inline=True)

            embed.add_field(
                name="2️⃣ Receber Cargo",
                value="Você receberá automaticamente o cargo de **Convidado**",
                inline=True)

            embed.add_field(name="3️⃣ Escolher Vocação (Obrigatório)",
                            value="Selecione sua vocação favorita:\n"
                            "🛡️ EK • 🔮 MS • 🏹 RP • 🌟 ED • 👊 MK",
                            inline=True)

            embed.add_field(name="ℹ️ Informações Importantes:",
                            value="• O processo é rápido e simples\n"
                            "• A seleção de vocação é obrigatória\n"
                            "• Você pode alterar sua vocação depois\n"
                            "• Em caso de dúvidas, fale com um administrador",
                            inline=False)

            embed.set_footer(
                text="Clique no botão abaixo para começar a verificação!",
                icon_url=interaction.guild.icon.url
                if interaction.guild.icon else None)

            # Criar view com botão
            view = VerificationPanelView()

            # Enviar painel
            message = await target_channel.send(embed=embed, view=view)

            # Resposta de confirmação
            embed_success = discord.Embed(
                title="✅ Painel Criado!",
                description=
                f"Painel de verificação criado com sucesso em {target_channel.mention}!",
                color=discord.Color.green())

            embed_success.add_field(
                name="📋 Informações:",
                value=f"• **Canal:** {target_channel.mention}\n"
                f"• **ID da Mensagem:** `{message.id}`\n"
                f"• **Cargos necessários:** Convidado, EK, MS, RP, ED, MK",
                inline=False)

            await interaction.response.send_message(embed=embed_success,
                                                    ephemeral=True)

            # Log
            logger.info(
                f"Painel de verificação criado - Admin: {interaction.user.id} ({interaction.user.name}) - Canal: {target_channel.id}"
            )

        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ Não tenho permissão para enviar mensagens neste canal!",
                ephemeral=True)
        except Exception as e:
            logger.error(
                f"Erro ao criar painel de verificação - Admin: {interaction.user.id} - Erro: {e}"
            )
            await interaction.response.send_message(
                "❌ Ocorreu um erro ao criar o painel. Verifique minhas permissões e tente novamente.",
                ephemeral=True)

    @app_commands.command(
        name="verificar_cargos",
        description="[ADMIN] Verificar se todos os cargos necessários existem")
    async def verificar_cargos(self, interaction: discord.Interaction):
        """Comando para verificar se os cargos necessários existem"""

        # Verificar permissões
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ Apenas administradores podem usar este comando!",
                ephemeral=True)
            return

        # Lista de cargos necessários
        cargos_necessarios = ["Convidado", "EK", "MS", "RP", "ED", "MK"]

        embed = discord.Embed(
            title="🔍 Verificação de Cargos",
            description="Verificando se todos os cargos necessários existem...",
            color=discord.Color.blue())

        cargos_encontrados = []
        cargos_faltando = []

        for cargo_nome in cargos_necessarios:
            cargo = discord.utils.get(interaction.guild.roles, name=cargo_nome)
            if cargo:
                cargos_encontrados.append(
                    f"✅ **{cargo_nome}** - {len(cargo.members)} membros")
            else:
                cargos_faltando.append(f"❌ **{cargo_nome}** - Não encontrado")

        if cargos_encontrados:
            embed.add_field(name="✅ Cargos Encontrados:",
                            value="\n".join(cargos_encontrados),
                            inline=False)

        if cargos_faltando:
            embed.add_field(name="❌ Cargos Faltando:",
                            value="\n".join(cargos_faltando),
                            inline=False)

            embed.add_field(name="🛠️ Como Criar:",
                            value="1. Vá em **Configurações do Servidor**\n"
                            "2. Clique em **Cargos**\n"
                            "3. Clique em **Criar Cargo**\n"
                            "4. Digite o nome exato do cargo\n"
                            "5. Configure as permissões conforme necessário",
                            inline=False)

            embed.color = discord.Color.orange()
        else:
            embed.add_field(
                name="🎉 Tudo Pronto!",
                value=
                "Todos os cargos necessários foram encontrados. O sistema de verificação está pronto para uso!",
                inline=False)
            embed.color = discord.Color.green()

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name="resultado_verificacao",
        description=
        "[ADMIN] Ver lista completa de todos os novos membros verificados")
    async def resultado_verificacao(self, interaction: discord.Interaction):
        """Comando para ver resultados das verificações"""

        # Verificar permissões
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ Apenas administradores podem usar este comando!",
                ephemeral=True)
            return

        try:
            storage = VerificationStorage()
            all_verifications = storage.get_all_verifications()

            if not all_verifications:
                embed = discord.Embed(
                    title="📋 Nenhuma Verificação Encontrada",
                    description=
                    "Ainda não há registros de verificações salvas.",
                    color=discord.Color.blue())
                await interaction.response.send_message(embed=embed,
                                                        ephemeral=True)
                return

            # Ordenar por data (mais recente primeiro)
            sorted_verifications = sorted(all_verifications,
                                          key=lambda x: x.get('timestamp', ''),
                                          reverse=True)

            # Criar embed principal
            embed = discord.Embed(
                title="📋 Lista Completa de Novos Membros Verificados",
                description=
                f"**Total de verificações:** {len(sorted_verifications)}\n\n",
                color=discord.Color.green())

            # Criar lista formatada
            lista_verificacoes = ""
            emoji_vocacoes = {
                "EK": "🛡️",
                "MS": "🔮",
                "RP": "🏹",
                "ED": "🌟",
                "MK": "👊",
                "Não selecionada": "❓"
            }

            for i, verification in enumerate(sorted_verifications, 1):
                data = verification.get('data', 'Data não disponível')
                nick_discord = verification.get('nick_discord', 'N/A')
                nick_servidor = verification.get('nick_atual_servidor',
                                                 'Não definido')
                vocacao = verification.get('vocacao', 'Não selecionada')
                status = verification.get('status', 'desconhecido')

                emoji_voc = emoji_vocacoes.get(vocacao, "❓")

                # Status emoji
                status_emoji = "✅" if status == "verificacao_concluida" else "⏳"

                lista_verificacoes += f"{status_emoji} **{i}.** {nick_servidor or nick_discord}\n"
                lista_verificacoes += f"      📅 **Data:** {data}\n"
                lista_verificacoes += f"      🏷️ **Nick Discord:** {nick_discord}\n"
                lista_verificacoes += f"      📝 **Nick Servidor:** {nick_servidor or 'Não definido'}\n"
                lista_verificacoes += f"      {emoji_voc} **Vocação:** {vocacao}\n\n"

                # Dividir em chunks se ficar muito longo
                if len(lista_verificacoes
                       ) > 3500:  # Deixar espaço para outros campos
                    break

            # Se a lista foi truncada
            if len(sorted_verifications) > i:
                lista_verificacoes += f"... e mais {len(sorted_verifications) - i} verificações.\n"
                lista_verificacoes += f"*Lista truncada devido ao limite de caracteres.*"

            embed.add_field(name="👥 Membros Verificados:",
                            value=lista_verificacoes if lista_verificacoes else
                            "Nenhum dado encontrado",
                            inline=False)

            # Estatísticas por vocação
            stats_vocacoes = {}
            stats_status = {}

            for verification in sorted_verifications:
                vocacao = verification.get('vocacao', 'Não selecionada')
                status = verification.get('status', 'desconhecido')

                stats_vocacoes[vocacao] = stats_vocacoes.get(vocacao, 0) + 1
                stats_status[status] = stats_status.get(status, 0) + 1

            # Adicionar estatísticas
            stats_text = ""
            for vocacao, count in stats_vocacoes.items():
                emoji = emoji_vocacoes.get(vocacao, "❓")
                stats_text += f"{emoji} {vocacao}: {count}\n"

            if stats_text:
                embed.add_field(name="📊 Estatísticas por Vocação:",
                                value=stats_text,
                                inline=True)

            # Status das verificações
            status_text = ""
            status_names = {
                "verificacao_iniciada": "⏳ Iniciada",
                "nickname_definido": "📝 Nick Definido",
                "verificacao_concluida": "✅ Concluída"
            }

            for status, count in stats_status.items():
                status_display = status_names.get(status, status)
                status_text += f"{status_display}: {count}\n"

            if status_text:
                embed.add_field(name="📈 Status das Verificações:",
                                value=status_text,
                                inline=True)

            embed.set_footer(
                text=
                f"💾 Dados salvos em verificacao.json • Comando executado por {interaction.user.display_name}",
                icon_url=interaction.user.display_avatar.url
                if interaction.user.display_avatar else None)

            await interaction.response.send_message(embed=embed,
                                                    ephemeral=True)

        except Exception as e:
            logger.error(f"Erro ao buscar resultados de verificação: {e}")
            await interaction.response.send_message(
                "❌ Erro ao carregar dados de verificação. Verifique os logs.",
                ephemeral=True)


async def setup(bot):
    await bot.add_cog(Verificacao(bot))