import discord
from discord.ext import commands
from discord import app_commands
from typing import List, Optional


class MemberManagementView(discord.ui.View):
    """View principal para gerenciamento de membros com cargo"""

    def __init__(self, role: discord.Role, guild: discord.Guild):
        super().__init__(timeout=300)
        self.role = role
        self.guild = guild
        self.members_with_role = []
        self.members_without_role = []
        self.selected_to_add = set()
        self.selected_to_remove = set()
        self.current_view = "overview"  # overview, add_view, remove_view

        self.load_members()
        self.setup_overview()

    def load_members(self):
        """Carregar e separar membros com e sem o cargo"""
        # Filtrar apenas bots reais, não usuários normais
        all_members = [
            member for member in self.guild.members if not member.bot
        ]

        print(
            f"[DEBUG] Total de membros no servidor: {len(self.guild.members)}")
        print(f"[DEBUG] Membros não-bot: {len(all_members)}")
        print(
            f"[DEBUG] Cargo sendo analisado: {self.role.name} (ID: {self.role.id})"
        )

        self.members_with_role = []
        self.members_without_role = []

        for member in all_members:
            if self.role in member.roles:
                self.members_with_role.append(member)
                print(f"[DEBUG] Membro COM cargo: {member.display_name}")
            else:
                self.members_without_role.append(member)
                print(f"[DEBUG] Membro SEM cargo: {member.display_name}")

        print(f"[DEBUG] Total com cargo: {len(self.members_with_role)}")
        print(f"[DEBUG] Total sem cargo: {len(self.members_without_role)}")

        # Ordenar por nome
        self.members_with_role.sort(key=lambda m: m.display_name.lower())
        self.members_without_role.sort(key=lambda m: m.display_name.lower())

    def setup_overview(self):
        """Configurar view de visão geral"""
        self.clear_items()
        self.current_view = "overview"

        # Botão para adicionar cargo (mostrar membros sem cargo)
        if self.members_without_role:
            add_button = discord.ui.Button(
                label=
                f"➕ Adicionar Cargo ({len(self.members_without_role)} disponíveis)",
                style=discord.ButtonStyle.success,
                emoji="➕")
            add_button.callback = self.show_add_view
            self.add_item(add_button)

        # Botão para remover cargo (mostrar membros com cargo)
        if self.members_with_role:
            remove_button = discord.ui.Button(
                label=
                f"➖ Remover Cargo ({len(self.members_with_role)} possuem)",
                style=discord.ButtonStyle.danger,
                emoji="➖")
            remove_button.callback = self.show_remove_view
            self.add_item(remove_button)

        # Botão para voltar à seleção de cargo
        back_button = discord.ui.Button(label="🔙 Escolher Outro Cargo",
                                        style=discord.ButtonStyle.secondary)
        back_button.callback = self.back_to_role_selection
        self.add_item(back_button)

    def setup_member_selection(self, action: str):
        """Configurar view para seleção de membros"""
        self.clear_items()
        self.current_view = f"{action}_view"

        members_list = self.members_without_role if action == "add" else self.members_with_role
        selected_set = self.selected_to_add if action == "add" else self.selected_to_remove

        if not members_list:
            return

        # Botão voltar
        back_button = discord.ui.Button(label="🔙 Voltar",
                                        style=discord.ButtonStyle.secondary)
        back_button.callback = self.back_to_overview
        self.add_item(back_button)

        # Botões de seleção em massa
        select_all_button = discord.ui.Button(
            label=f"✅ Selecionar Todos ({len(members_list)})",
            style=discord.ButtonStyle.primary)
        select_all_button.callback = lambda i: self.select_all_members(
            i, action)
        self.add_item(select_all_button)

        if selected_set:
            deselect_button = discord.ui.Button(
                label="❌ Desmarcar Todos", style=discord.ButtonStyle.secondary)
            deselect_button.callback = lambda i: self.deselect_all_members(
                i, action)
            self.add_item(deselect_button)

        # Botão de confirmação
        if selected_set:
            action_text = "Adicionar Cargo" if action == "add" else "Remover Cargo"
            confirm_button = discord.ui.Button(
                label=f"🔧 {action_text} ({len(selected_set)})",
                style=discord.ButtonStyle.success)
            confirm_button.callback = lambda i: self.confirm_action(i, action)
            self.add_item(confirm_button)

        # Dropdowns para seleção de membros (máximo 25 por vez)
        for i in range(0, len(members_list), 25):
            batch = members_list[i:i + 25]
            batch_num = (i // 25) + 1
            total_batches = ((len(members_list) - 1) // 25) + 1

            options = []
            for member in batch:
                is_selected = member.id in selected_set
                emoji = "✅" if is_selected else "⬜"
                prefix = "[SELECIONADO] " if is_selected else ""

                display_name = member.display_name
                if len(display_name) > 35:
                    display_name = display_name[:32] + "..."

                options.append(
                    discord.SelectOption(label=f"{prefix}{display_name}",
                                         description=f"ID: {member.id}",
                                         value=str(member.id),
                                         emoji=emoji))

            placeholder = f"📋 Membros {batch_num}/{total_batches}" if total_batches > 1 else "📋 Selecionar membros"

            select = discord.ui.Select(placeholder=placeholder,
                                       options=options,
                                       max_values=len(options))
            select.callback = lambda i, a=action: self.member_select_callback(
                i, a)
            self.add_item(select)

    async def show_add_view(self, interaction: discord.Interaction):
        """Mostrar view para adicionar cargo"""
        self.setup_member_selection("add")
        embed = self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def show_remove_view(self, interaction: discord.Interaction):
        """Mostrar view para remover cargo"""
        self.setup_member_selection("remove")
        embed = self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def back_to_overview(self, interaction: discord.Interaction):
        """Voltar para visão geral"""
        self.setup_overview()
        embed = self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def back_to_role_selection(self, interaction: discord.Interaction):
        """Voltar para seleção de cargo"""
        embed = discord.Embed(title="🔧 Gerenciar Cargos em Massa",
                              description="Selecione um cargo para gerenciar:",
                              color=discord.Color.blue())

        view = RoleSelectView(self.guild)
        await interaction.response.edit_message(embed=embed, view=view)

    async def member_select_callback(self, interaction: discord.Interaction,
                                     action: str):
        """Callback para seleção de membros"""
        try:
            selected_ids = set(
                int(value) for value in interaction.data['values'])
            selected_set = self.selected_to_add if action == "add" else self.selected_to_remove

            # Toggle seleção
            for member_id in selected_ids:
                if member_id in selected_set:
                    selected_set.remove(member_id)
                else:
                    selected_set.add(member_id)

            self.setup_member_selection(action)
            embed = self.create_embed()
            await interaction.response.edit_message(embed=embed, view=self)

        except Exception as e:
            print(f"Erro na seleção: {e}")
            await interaction.response.send_message(
                "❌ Erro ao processar seleção!", ephemeral=True)

    async def select_all_members(self, interaction: discord.Interaction,
                                 action: str):
        """Selecionar todos os membros"""
        members_list = self.members_without_role if action == "add" else self.members_with_role
        selected_set = self.selected_to_add if action == "add" else self.selected_to_remove

        selected_set.update(member.id for member in members_list)
        self.setup_member_selection(action)
        embed = self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def deselect_all_members(self, interaction: discord.Interaction,
                                   action: str):
        """Desmarcar todos os membros"""
        selected_set = self.selected_to_add if action == "add" else self.selected_to_remove
        selected_set.clear()
        self.setup_member_selection(action)
        embed = self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def confirm_action(self, interaction: discord.Interaction,
                             action: str):
        """Confirmar e executar ação"""
        selected_set = self.selected_to_add if action == "add" else self.selected_to_remove

        if not selected_set:
            await interaction.response.send_message(
                "❌ Nenhum membro selecionado!", ephemeral=True)
            return

        action_text = "adicionar o cargo" if action == "add" else "remover o cargo"
        embed = discord.Embed(
            title="⚠️ Confirmação",
            description=
            f"Você está prestes a **{action_text}** `{self.role.name}` para **{len(selected_set)}** membros.\n\n✅ **Confirmar** para continuar\n❌ **Cancelar** para voltar",
            color=discord.Color.orange())

        view = ConfirmActionView(selected_set, self.role, action, self.guild)
        await interaction.response.edit_message(embed=embed, view=view)

    def create_embed(self) -> discord.Embed:
        """Criar embed baseado na view atual"""
        embed = discord.Embed(
            title=f"🔧 Gerenciar Cargo: {self.role.name}",
            color=self.role.color if self.role.color
            != discord.Color.default() else discord.Color.blue())

        if self.current_view == "overview":
            embed.description = f"**🏷️ Cargo:** {self.role.mention}\n\n"
            embed.description += f"**📊 Estatísticas do Servidor:**\n"
            embed.description += f"👥 **Total de membros:** {len(self.members_with_role) + len(self.members_without_role)}\n"
            embed.description += f"✅ **Com o cargo:** {len(self.members_with_role)}\n"
            embed.description += f"❌ **Sem o cargo:** {len(self.members_without_role)}\n\n"
            embed.description += "**Escolha uma ação:**"

            if self.members_with_role:
                # Mostrar alguns membros que têm o cargo
                member_names = [
                    m.display_name for m in self.members_with_role[:8]
                ]
                members_text = ", ".join(member_names)
                if len(self.members_with_role) > 8:
                    members_text += f" (+{len(self.members_with_role) - 8} mais)"

                embed.add_field(name="✅ Membros com o cargo:",
                                value=members_text,
                                inline=False)

            if self.members_without_role:
                # Mostrar alguns membros que não têm o cargo
                member_names = [
                    m.display_name for m in self.members_without_role[:8]
                ]
                members_text = ", ".join(member_names)
                if len(self.members_without_role) > 8:
                    members_text += f" (+{len(self.members_without_role) - 8} mais)"

                embed.add_field(name="❌ Membros sem o cargo:",
                                value=members_text,
                                inline=False)

        elif self.current_view == "add_view":
            embed.title = f"➕ Adicionar Cargo: {self.role.name}"
            embed.description = f"**🏷️ Cargo:** {self.role.mention}\n"
            embed.description += f"**👥 Membros disponíveis:** {len(self.members_without_role)}\n"
            embed.description += f"**✅ Selecionados:** {len(self.selected_to_add)}\n\n"
            embed.description += "**Selecione os membros para adicionar o cargo:**"

            if self.selected_to_add:
                selected_names = []
                for member_id in list(self.selected_to_add)[:10]:
                    member = discord.utils.get(self.members_without_role,
                                               id=member_id)
                    if member:
                        selected_names.append(member.display_name)

                selected_text = ", ".join(selected_names)
                if len(self.selected_to_add) > 10:
                    selected_text += f" (+{len(self.selected_to_add) - 10} mais)"

                embed.add_field(name="✅ Selecionados para adicionar:",
                                value=selected_text,
                                inline=False)

        elif self.current_view == "remove_view":
            embed.title = f"➖ Remover Cargo: {self.role.name}"
            embed.description = f"**🏷️ Cargo:** {self.role.mention}\n"
            embed.description += f"**👥 Membros com cargo:** {len(self.members_with_role)}\n"
            embed.description += f"**✅ Selecionados:** {len(self.selected_to_remove)}\n\n"
            embed.description += "**Selecione os membros para remover o cargo:**"

            if self.selected_to_remove:
                selected_names = []
                for member_id in list(self.selected_to_remove)[:10]:
                    member = discord.utils.get(self.members_with_role,
                                               id=member_id)
                    if member:
                        selected_names.append(member.display_name)

                selected_text = ", ".join(selected_names)
                if len(self.selected_to_remove) > 10:
                    selected_text += f" (+{len(self.selected_to_remove) - 10} mais)"

                embed.add_field(name="✅ Selecionados para remover:",
                                value=selected_text,
                                inline=False)

        embed.set_footer(
            text="Use os dropdowns para selecionar/desmarcar membros")
        return embed


class ConfirmActionView(discord.ui.View):
    """View de confirmação da ação"""

    def __init__(self, selected_member_ids: set, role: discord.Role,
                 action: str, guild: discord.Guild):
        super().__init__(timeout=60)
        self.selected_member_ids = selected_member_ids
        self.role = role
        self.action = action
        self.guild = guild

    @discord.ui.button(label="✅ Confirmar", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction,
                      button: discord.ui.Button):
        """Executar a ação confirmada"""
        await interaction.response.defer()

        success_count = 0
        error_count = 0
        errors = []
        processed_members = []

        action_text = "adicionado" if self.action == "add" else "removido"

        # Processar cada membro
        for member_id in self.selected_member_ids:
            member = self.guild.get_member(member_id)
            if not member:
                error_count += 1
                errors.append(f"Membro ID {member_id} não encontrado")
                continue

            try:
                if self.action == "add":
                    if self.role not in member.roles:
                        await member.add_roles(
                            self.role,
                            reason=f"Adição em massa por {interaction.user}")
                        success_count += 1
                        processed_members.append(f"✅ {member.display_name}")
                    else:
                        errors.append(
                            f"{member.display_name}: Já possui o cargo")
                else:  # remove
                    if self.role in member.roles:
                        await member.remove_roles(
                            self.role,
                            reason=f"Remoção em massa por {interaction.user}")
                        success_count += 1
                        processed_members.append(f"✅ {member.display_name}")
                    else:
                        errors.append(
                            f"{member.display_name}: Não possui o cargo")

            except discord.Forbidden:
                error_count += 1
                errors.append(f"{member.display_name}: Sem permissão")
            except discord.HTTPException as e:
                error_count += 1
                errors.append(f"{member.display_name}: Erro HTTP")
            except Exception as e:
                error_count += 1
                errors.append(f"{member.display_name}: Erro inesperado")

        # Criar embed de resultado
        embed = discord.Embed(title="✅ Ação Concluída!" if error_count == 0
                              else "⚠️ Ação Concluída com Avisos",
                              color=discord.Color.green()
                              if error_count == 0 else discord.Color.orange())

        embed.description = f"**🏷️ Cargo:** {self.role.mention}\n"
        embed.description += f"**🔧 Ação:** Cargo {action_text}\n"
        embed.description += f"**✅ Sucessos:** {success_count}\n"
        embed.description += f"**⚠️ Erros/Avisos:** {error_count}"

        if processed_members:
            members_text = "\n".join(processed_members[:15])
            if len(processed_members) > 15:
                members_text += f"\n... e mais {len(processed_members) - 15} membros"
            embed.add_field(name="✅ Processados com sucesso:",
                            value=members_text,
                            inline=False)

        if errors:
            error_text = "\n".join(errors[:10])
            if len(errors) > 10:
                error_text += f"\n... e mais {len(errors) - 10} erros"
            embed.add_field(name="⚠️ Erros/Avisos:",
                            value=error_text,
                            inline=False)

        await interaction.followup.edit_message(interaction.message.id,
                                                embed=embed,
                                                view=None)

    @discord.ui.button(label="❌ Cancelar", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction,
                     button: discord.ui.Button):
        """Cancelar a ação"""
        embed = discord.Embed(
            title="❌ Ação Cancelada",
            description="A operação foi cancelada pelo usuário.",
            color=discord.Color.red())
        await interaction.response.edit_message(embed=embed, view=None)


class RoleSelectView(discord.ui.View):
    """View para seleção do cargo"""

    def __init__(self, guild: discord.Guild):
        super().__init__(timeout=300)
        self.guild = guild
        self.setup_role_select()

    def setup_role_select(self):
        """Configurar o dropdown de seleção de cargos"""
        # Filtrar cargos (excluir @everyone e cargos de bot)
        roles = [
            role for role in self.guild.roles
            if role != self.guild.default_role and not role.managed
            and role.name != "@everyone"
        ]

        # Ordenar por posição (hierarquia)
        roles.sort(key=lambda r: r.position, reverse=True)

        # Limitar a 25 cargos (limite do Discord)
        if len(roles) > 25:
            roles = roles[:25]

        if not roles:
            return

        options = []
        for role in roles:
            # Contar membros com o cargo
            member_count = len(role.members)

            options.append(
                discord.SelectOption(
                    label=role.name,
                    description=
                    f"{member_count} membros • Pos: {role.position}",
                    value=str(role.id),
                    emoji="🏷️"))

        select = discord.ui.Select(
            placeholder="🏷️ Selecione o cargo para gerenciar...",
            options=options)
        select.callback = self.role_select_callback
        self.add_item(select)

    async def role_select_callback(self, interaction: discord.Interaction):
        """Callback para seleção do cargo"""
        try:
            role_id = int(interaction.data['values'][0])
            role = self.guild.get_role(role_id)

            print(
                f"[DEBUG] Cargo selecionado: {role.name if role else 'None'} (ID: {role_id})"
            )
            print(f"[DEBUG] Guild: {self.guild.name} (ID: {self.guild.id})")
            print(
                f"[DEBUG] Total de membros na guild: {len(self.guild.members)}"
            )

            if not role:
                await interaction.response.send_message(
                    "❌ Cargo não encontrado!", ephemeral=True)
                return

            # Verificar permissões
            if role.position >= interaction.user.top_role.position and interaction.user != interaction.guild.owner:
                await interaction.response.send_message(
                    f"❌ Você não pode gerenciar o cargo {role.mention} pois ele está acima do seu cargo mais alto!",
                    ephemeral=True)
                return

            if role.position >= interaction.guild.me.top_role.position:
                bot_highest_role = interaction.guild.me.top_role
                await interaction.response.send_message(
                    f"❌ **Erro de Hierarquia de Cargos**\n\n"
                    f"Não posso gerenciar o cargo {role.mention} pois ele está acima do meu cargo mais alto.\n\n"
                    f"**Meu cargo mais alto:** {bot_highest_role.mention} (Posição: {bot_highest_role.position})\n"
                    f"**Cargo solicitado:** {role.mention} (Posição: {role.position})\n\n"
                    f"**Como resolver:**\n"
                    f"1. Vá em **Configurações do Servidor** → **Cargos**\n"
                    f"2. Arraste meu cargo ({bot_highest_role.mention}) para **acima** de {role.mention}\n"
                    f"3. Ou mova {role.mention} para **abaixo** do meu cargo",
                    ephemeral=True)
                return

            # Mostrar interface de gerenciamento
            view = MemberManagementView(role, self.guild)
            embed = view.create_embed()
            await interaction.response.edit_message(embed=embed, view=view)

        except Exception as e:
            print(f"Erro na seleção de cargo: {e}")
            import traceback
            print(f"Traceback completo: {traceback.format_exc()}")
            await interaction.response.send_message(
                "❌ Erro ao processar seleção!", ephemeral=True)


class GerenciarCargos(commands.Cog):
    """Cog para gerenciamento de cargos em massa"""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="gerenciar_cargos",
        description=
        "Adicionar ou remover cargos de múltiplos membros de uma vez")
    @app_commands.describe(cargo="Cargo específico para gerenciar (opcional)")
    async def gerenciar_cargos_slash(self,
                                     interaction: discord.Interaction,
                                     cargo: Optional[discord.Role] = None):
        """Comando principal para gerenciar cargos em massa"""

        # Verificar permissões do usuário
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message(
                "❌ Você precisa da permissão **Gerenciar Cargos** para usar este comando!",
                ephemeral=True)
            return

        # Verificar permissões do bot
        if not interaction.guild.me.guild_permissions.manage_roles:
            await interaction.response.send_message(
                "❌ Eu preciso da permissão **Gerenciar Cargos** para executar este comando!",
                ephemeral=True)
            return

        # Debug: Verificar se o bot pode ver os membros
        print(f"[DEBUG] Comando iniciado por: {interaction.user.display_name}")
        print(f"[DEBUG] Guild: {interaction.guild.name}")
        print(
            f"[DEBUG] Total de membros visíveis: {len(interaction.guild.members)}"
        )
        print(
            f"[DEBUG] Bot tem permissão para ver membros: {self.bot.intents.members}"
        )

        # Se não conseguir ver membros, tentar carregar
        if len(interaction.guild.members) <= 1:  # Só o bot
            try:
                print("[DEBUG] Tentando carregar membros...")
                await interaction.guild.chunk()
                print(
                    f"[DEBUG] Após chunk: {len(interaction.guild.members)} membros"
                )
            except Exception as e:
                print(f"[DEBUG] Erro ao fazer chunk: {e}")
                await interaction.response.send_message(
                    "❌ Não consigo acessar a lista de membros do servidor. Verifique se tenho as permissões necessárias (Server Members Intent).",
                    ephemeral=True)
                return

        # Se um cargo específico foi fornecido
        if cargo:
            # Verificar se o usuário pode gerenciar este cargo
            if cargo.position >= interaction.user.top_role.position and interaction.user != interaction.guild.owner:
                await interaction.response.send_message(
                    f"❌ Você não pode gerenciar o cargo {cargo.mention} pois ele está acima do seu cargo mais alto!",
                    ephemeral=True)
                return

            # Verificar se o bot pode gerenciar este cargo
            if cargo.position >= interaction.guild.me.top_role.position:
                await interaction.response.send_message(
                    f"❌ Eu não posso gerenciar o cargo {cargo.mention} pois ele está acima do meu cargo mais alto!",
                    ephemeral=True)
                return

            # Ir direto para gerenciamento do cargo
            view = MemberManagementView(cargo, interaction.guild)
            embed = view.create_embed()
            await interaction.response.send_message(embed=embed,
                                                    view=view,
                                                    ephemeral=True)
        else:
            # Mostrar seleção de cargos
            embed = discord.Embed(
                title="🔧 Gerenciar Cargos em Massa",
                description="**Selecione um cargo para gerenciar:**\n\n"
                "🔹 **Como funciona:**\n"
                "• Escolha o cargo que deseja gerenciar\n"
                "• Veja quem tem e quem não tem o cargo\n"
                "• Selecione membros para adicionar ou remover\n"
                "• Confirme as alterações",
                color=discord.Color.blue())

            view = RoleSelectView(interaction.guild)

            if not view.children:
                await interaction.response.send_message(
                    "❌ Nenhum cargo disponível para gerenciar neste servidor!",
                    ephemeral=True)
                return

            await interaction.response.send_message(embed=embed,
                                                    view=view,
                                                    ephemeral=True)


async def setup(bot):
    await bot.add_cog(GerenciarCargos(bot))