# -- coding: shift_jis --
# py-cordとその拡張機能をインポート
#from email import header
import discord
from discord.ext import commands
from discord.types import channel
import psycopg2

import os.path
import json
from google.auth import credentials
import googleapiclient.errors
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_get_credential import google_get_credential


# データベースの情報を設定
db_host = "127.0.0.1"
db_name = "DBNAME"
db_user = "USER"
db_password = "PASSWORD"

# データベースに接続する関数を定義する
def connect_db():
    # データベースに接続してコネクションとカーソルを返す
    conn = psycopg2.connect(host=db_host, database=db_name, user=db_user, password=db_password)
    cur = conn.cursor()
    return conn, cur


bot = discord.Bot(
    
)

# Cogクラスを定義
class ListP(commands.Cog):
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
    
    # list_pコマンドを実装
    @bot.command(name="list_p", description="データベース内にあるプレイリストを一覧表示します")
    async def list_p(self, ctx): # デフォルト値をNoneにする
        
            conn, cur = connect_db()

            # SQL文を作成
            sql = "SELECT playlist_id,playlist_name, playlist_link, record_id FROM playlist_info_table"

            # SQL文を実行して結果を取得
            cur.execute(sql)
            result = cur.fetchall()

            # 結果が空でなければ、プレイリスト名とリンクの表を作成してメッセージを表示
            if result:
                
                # embedの内容を作成
                for row in result:
                    
                    #YoutubeDataApiからプレイリストのサムネイル画像urlを取得
                    youtube = google_get_credential.get_credentials()
                    response = youtube.playlists().list(id=row[0], part="snippet").execute()
                    playlist_thumb = response["items"][0]["snippet"]["thumbnails"]["default"]["url"]
                    
                    # embedオブジェクトを作成
                    embed = discord.Embed(title=f"{row[1]}", url=row[2], description=f"ID:{row[0]}", color=0xB6BAB7)
                    embed.set_thumbnail(url=playlist_thumb)
                    
                    # DBからプレイリスト内の動画数を取得
                    sql = "SELECT record_id FROM playlist_video_relation_table WHERE playlist_record_id = %s"
                    # SQL文を実行して結果を取得
                    cur.execute(sql, (row[3],))
                    result_v = cur.fetchall()
                    video_quant = len(result_v)
                    #print(video_quant)
                    embed.add_field(name=f"動画数：{video_quant}",value="", inline=False)
                    
                    await ctx.respond(embed=embed)   
            else:
                # 結果が空ならば、データベースにプレイリストが存在しないというメッセージを表示
                await ctx.respond("データベースにプレイリストが存在しません。")
            return

# CogオブジェクトをBotオブジェクトに登録するための関数
def setup(bot):
    bot.add_cog(ListP(bot))

