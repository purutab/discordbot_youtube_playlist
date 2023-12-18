# -- coding: shift_jis --
# py-cordとその拡張機能をインポート
import imp
from sqlite3 import Row
from urllib import response
import discord
from discord.ext import commands
from discord.types import channel
import psycopg2

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



#文字数の上限
max_length = 18
#省略記号
ellipsis = "…"
#文字数を切り詰める関数
def truncate(string, length, ellipsis):
    #文字数が上限以下ならそのまま返す
    if len(string) <= length:
        return string
    #文字数が上限より多いなら、上限までの文字と省略記号を返す
    else:
        return string[:length - len(ellipsis)] + ellipsis
    

bot = discord.Bot(
    
)

# Cogクラスを定義
class ListV(commands.Cog):
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
    @bot.command(name="list_v", description="指定したプレイリスト内の動画を一覧表示します。")
    async def list_v(self, ctx: discord.ApplicationContext, playlist_name: str): # デフォルト値をNoneにする
        
        conn, cur = connect_db()

        if playlist_name is not None:
        #playlist名からrecord_idを検索する
            sql = "SELECT record_id,playlist_id FROM playlist_info_table WHERE playlist_name = %s"
            
            # SQL文を実行して結果を取得
            cur.execute(sql, (playlist_name,))
            result_p = cur.fetchall()
            result_count_p = len(result_p)
            #print(result_p)

        #検索結果件数が1でなかった際、ユーザーに通知    
        if result_count_p >= 2:
            await ctx.respond("同一名プレイリストが複数ありますので、プレイリストidでの検索をお願いします。")
        
        elif result_count_p == 1:
            playlist_r_id = tuple(x[0] for x in result_p)
            playlist_id = tuple(x[1] for x in result_p)[0]
            #print(playlist_r_id)
            #print(playlist_id)
            #プレイリスト内にあるvideo_record_idを取得
            sql = "SELECT video_record_id FROM playlist_video_relation_table WHERE playlist_record_id = %s"
            
            # SQL文を実行して結果を取得
            cur.execute(sql, (playlist_r_id,))
            result_v = cur.fetchall()
            
            #video_record_idから対象動画情報を取得
            sql = "SELECT * FROM video_info_table WHERE record_id in %s"
            video_r_id = tuple(x[0] for x in result_v)
            
            # SQL文を実行して結果を取得
            cur.execute(sql, (video_r_id,))
            result = cur.fetchall()
            result_count = len(result)
            
            if result:
                #表の内容を作成
                content = ""
                count = 0 #行数をカウントする変数
                limit = 10 #一つのフィールドに入れる行数の上限
                total = 0 #文字数をカウントする変数
                max_total = 5000 #一つのembedに入れる文字数の上限
                field_num = 1 #フィールドの番号を示す変数
                embed_num = 1 #embedの番号を示す変数
                
                #YoutubeDataApiからプレイリストのサムネイル画像urlを取得
                youtube = google_get_credential.get_credentials()
                response = youtube.playlists().list(id=playlist_id, part="snippet").execute()
                playlist_thumb = response["items"][0]["snippet"]["thumbnails"]["default"]["url"]
                
                #embedオブジェクトを作成
                embed = discord.Embed(title=f"{playlist_name}内の動画一覧",description=" 動画名 | 追加したチャンネル | 再生時間 ",color=0xB6BAB7)
                embed.set_footer(text=f"{playlist_name}, aggregated by {self.bot.user.name}", icon_url=playlist_thumb)
                for row in result:
                    content += f"- [{row[1]}]({row[2]}) | {row[5]} | {row[3]}\n" 
                    count += 1 #行数を増やす
                    
                    if total >= max_total:#文字数が上限に達したとき、新しいembedを作成する
                        await ctx.respond(embed=embed)
                        embed_num += 1
                        embed = discord.Embed(title=f"{playlist_name}内の動画一覧その{embed_num}",description=" 動画名 | 追加したチャンネル | 再生時間 ",color=0xB6BAB7)
                        embed.set_footer(text=f"{playlist_name}, aggregated by {self.bot.user.name}", icon_url=playlist_thumb)
                        total = 0
                    
                    if count == limit: #行数が上限に達したら
                        #フィールドの名前に動画表示範囲を設定
                        field_name = f"動画 {limit * (field_num - 1) + 1}～{limit * field_num}" 
                        #フィールドに追加してcontentとcountをリセットする
                        embed.add_field(name=field_name, value=content, inline=False)
                        total += len(content)
                        print(total)
                        content = ""
                        count = 0
                        field_num += 1 #フィールド番号を増やす
                        
                   
                #最後に残ったcontentをフィールドに追加する
                if content:
                    embed.add_field(name=f"動画 {limit * (field_num - 1) + 1}～{limit * (field_num -1) + count}", value=content, inline=False)
    
                await ctx.respond(embed=embed)
            else:
                await ctx.respond(f"おっと。{playlist_name}にまだ動画がないか、データベースに登録されていないようですねぇ。")
                
        elif playlist_name is not None:
        #プレイリストidから検索を行う
            sql = "SELECT record_id,playlist_name,playlist_id FROM playlist_info_table WHERE playlist_id = %s"
            
            # SQL文を実行して結果を取得
            cur.execute(sql, (playlist_name,))
            result_p = cur.fetchall()
            
            if result_p:
                playlist_r_id = tuple(x[0] for x in result_p)[0]
                playlist_DBname = tuple(x[1] for x in result_p)[0]
                playlist_id = tuple(x[2] for x in result_p)[0]
                
                #プレイリスト内にあるvideo_record_idを取得
                sql = "SELECT video_record_id FROM playlist_video_relation_table WHERE playlist_record_id = %s"
            
                # SQL文を実行して結果を取得
                cur.execute(sql, (playlist_r_id,))
                result_v = cur.fetchall()
            
                #video_record_idから対象動画情報を取得
                sql = "SELECT * FROM video_info_table WHERE record_id in %s"
                video_r_id = tuple(x[0] for x in result_v)
            
                # SQL文を実行して結果を取得
                cur.execute(sql, (video_r_id,))
                result = cur.fetchall()
                result_count = len(result)
            
                if result:
                    #表の内容を作成
                    content = ""
                    count = 0 #行数をカウントする変数
                    limit = 10 #一つのフィールドに入れる行数の上限
                    total = 0 #文字数をカウントする変数
                    max_total = 5000 #一つのembedに入れる文字数の上限
                    field_num = 1 #フィールドの番号を示す変数
                    embed_num = 1 #embedの番号を示す変数
                
                    #YoutubeDataApiからプレイリストのサムネイル画像urlを取得
                    youtube = google_get_credential.get_credentials()
                    response = youtube.playlists().list(id=playlist_id, part="snippet").execute()
                    playlist_thumb = response["items"][0]["snippet"]["thumbnails"]["default"]["url"]
                
                    #embedオブジェクトを作成
                    embed = discord.Embed(title=f"{playlist_DBname}内の動画一覧",description=" 動画名 | 追加したチャンネル | 再生時間 ",color=0xB6BAB7)
                    embed.set_footer(text=f"{playlist_name}, aggregated by {self.bot.user.name}", icon_url=playlist_thumb)
                    for row in result:
                        content += f"- [{row[1]}]({row[2]}) | {row[5]} | {row[3]}\n" 
                        count += 1 #行数を増やす
                    
                        if total >= max_total:#文字数が上限に達したとき、新しいembedを作成する
                            await ctx.respond(embed=embed)
                            embed_num += 1
                            embed = discord.Embed(title=f"{playlist_DBname}内の動画一覧その{embed_num}",description=" 動画名 | 追加したチャンネル | 再生時間 ",color=0xB6BAB7)
                            embed.set_footer(text=f"{playlist_name}, aggregated by {self.bot.user.name}", icon_url=playlist_thumb)
                            total = 0
                    
                        if count == limit: #行数が上限に達したら
                            #フィールドの名前に動画表示範囲を設定
                            field_name = f"動画 {limit * (field_num - 1) + 1}～{limit * field_num}" 
                            #フィールドに追加してcontentとcountをリセットする
                            embed.add_field(name=field_name, value=content, inline=False)
                            total += len(content)
                            print(total)
                            content = ""
                            count = 0
                            field_num += 1 #フィールド番号を増やす
                        
                   
                    #最後に残ったcontentをフィールドに追加する
                    if content:
                        embed.add_field(name=f"動画 {limit * (field_num - 1) + 1}～{limit * (field_num -1) + count}", value=content, inline=False)
    
                    await ctx.respond(embed=embed)
            else:
                await ctx.respond(f"おっと。{playlist_name}にまだ動画がないか、データベースに登録されていないようですねぇ。")
        

# CogオブジェクトをBotオブジェクトに登録するための関数
def setup(bot):
    bot.add_cog(ListV(bot))

