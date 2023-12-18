# -- coding: shift_jis --
# py-cordとその拡張機能をインポート
import discord
from discord.ext import commands


bot = discord.Bot(
    
)

# Cogクラスを定義
class VersionP(commands.Cog):
    # Cogオブジェクトが作成される際に呼び出されるメソッド
    def __init__(self, bot):
        # Botオブジェクトへの参照を保存
        self.bot = bot

    # Cog内のコマンドが実行される前に呼び出されるメソッド
    async def cog_check(self, ctx):
        # コマンドがテキストチャンネルで実行されたかどうかをチェック
        if not isinstance(ctx.channel, discord.TextChannel):
            # テキストチャンネル以外ではエラーメッセージを送信してコマンドをキャンセル
            await ctx.send("このコマンドはテキストチャンネルでのみ使用できます。")
            return False
        # テキストチャンネルであればコマンドを実行
        return True

    # /version_pというコマンドを定義
    @bot.command(name="version_p", description="Botのリリースノート表示")
    async def version_p(self, ctx):
        # Botの名前とバージョンナンバーを取得
        bot_name = self.bot.user.name
        bot_version = "2.0.0"

        # release_notesフォルダ内のテキストファイルから変更点を読み込む
        with open(f"release_notes/{bot_version}.txt", "r", encoding="utf-8") as f:
            notes = f.read()

        # テキストファイルから読み込んだ内容を区切り文字で分割する
        notes = notes.split("#")

        # embedオブジェクトを作成
        embed = discord.Embed(title=f"*{bot_name} ver.{bot_version}リリース！*",color=0xB6BAB7)
        embed.add_field(name="アップデート概要", value=notes[1], inline=False) # ボタンを押さずとも表示される内容

        # ボットに関わる情報を取得
        bot_info = notes[6]
        bot_author = bot_info.split("：")[2].split("￥")[0] # 作成者の名前とユーザーID
        bot_release = bot_info.split("￥")[1] # リリース日時

        # 作成者の名前とユーザーIDからユーザーリンクを作成
        bot_author_link = f"[{bot_author}](https://discordapp.com/users/AUTHOR_UID_HERE)"

        # embedにBot_infoという項目を追加して、ボットに関わる情報を表示する
        embed.add_field(name="Bot_info", value=f"・作成者：{bot_author_link}\n- リリース日時：{bot_release}", inline=False)

        # viewオブジェクトを作成するためのカスタムクラスを定義
        class VersionPView(discord.ui.View):
            def __init__(self):
                super().__init__()
                # ビューに詳細フラグを追加して、詳細な情報が表示されているかどうかを管理する
                self.detail = False

            # ボタンが押された時に実行されるコールバック関数を定義する
            @discord.ui.button(label="詳細な情報を表示/非表示", style=discord.ButtonStyle.primary)
            async def button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
                # ビューの詳細フラグを反転させる
                self.detail = not self.detail
                # 詳細フラグがTrueなら、embedに詳細な情報を追加する
                if self.detail:
                    embed.insert_field_at(1,name="修正点", value=notes[2].split("'")[1], inline=False) # 修正点の内容
                    embed.insert_field_at(2,name="コード変更", value=notes[3].split("'")[1], inline=False) # コード変更の内容
                    embed.insert_field_at(3,name="開発中要素", value=notes[4].split("'")[1], inline=False) # 開発中要素の内容
                    embed.insert_field_at(4,name="その他", value=notes[5].split("'")[1], inline=False)
                # 詳細フラグがFalseなら、embedから詳細な情報を削除する
                else:
                    for i in range(4):
                        embed.remove_field(1) # 修正点からその他までの項目を削除する
        
                # embedを更新して送信する
                await interaction.response.edit_message(embed=embed)
        
                

        # viewオブジェクトを作成する
        view = VersionPView()

        # embedとviewをメッセージに添付して送信する
        await ctx.respond("こちらが濃厚Botアップデートさんの、濃厚アップデート内容です", embed=embed, view=view)

# CogオブジェクトをBotオブジェクトに登録するための関数
def setup(bot):
    bot.add_cog(VersionP(bot))
