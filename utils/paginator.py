import disnake

class PaginationView(disnake.ui.View):
    """Paginated results view"""
    def __init__(self, embeds):
        super().__init__(timeout=60)
        self.embeds = embeds
        self.current_page = 0
        
    @disnake.ui.button(label="◀", style=disnake.ButtonStyle.gray)
    async def previous_button(self, button: disnake.ui.Button, interaction: disnake.Interaction):
        self.current_page = max(0, self.current_page - 1)
        await interaction.response.edit_message(embed=self.embeds[self.current_page])
        
    @disnake.ui.button(label="▶", style=disnake.ButtonStyle.gray)
    async def next_button(self, button: disnake.ui.Button, interaction: disnake.Interaction):
        self.current_page = min(len(self.embeds)-1, self.current_page + 1)
        await interaction.response.edit_message(embed=self.embeds[self.current_page])