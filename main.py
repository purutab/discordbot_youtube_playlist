#!/usr/bin/python
# -- coding: shift_jis --
# main.py
import discord
from discord.ext import commands # commandsをインポートする
import re
import psycopg2
import random
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import os.path
import pickle
import time

# version_p.pyファイルからVersionPクラスをインポート
from commands.version_p import VersionP

# APIキーとサービス名、バージョンを設定
API_KEY = ""
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# 認証情報が含まれるJSONファイルの名前とスコープを設定
CLIENT_SECRETS_FILE = "client_secret_DiscordBot_youtube_playlist.json"
SCOPES = ["https://www.googleapis.com/auth/youtube"]

# 認証情報を保存するファイル名を設定
CREDENTIALS_FILE = "credentials.json"

# 認証情報が保存されているかチェック
if os.path.exists(CREDENTIALS_FILE):
    # 保存されている場合は読み込む
    with open(CREDENTIALS_FILE, "rb") as f:
        credentials = pickle.load(f)
else:
    # 保存されていない場合は新規に作成する
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    credentials = flow.run_local_server(port=0)
    # 作成した認証情報を保存する
    with open(CREDENTIALS_FILE, "wb") as f:
        pickle.dump(credentials, f)

# 認証情報が有効期限切れかチェック
if credentials.expired:
    # 有効期限切れの場合はトークンをリフレッシュする
    credentials.refresh(Request())

# 認証情報を使ってYouTube APIクライアントを作成する
youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, credentials=credentials)

# データベースの情報を設定
db_host = "127.0.0.1"
db_name = "discordbot_youtube_playlist2"
db_user = "USER"
db_password = "PASSWORD"


# データベースに接続する関数を定義する
def connect_db():
    # データベースに接続してコネクションとカーソルを返す
    conn = psycopg2.connect(host=db_host, database=db_name, user=db_user, password=db_password)
    cur = conn.cursor()
    return conn, cur



# アクセストークンを設定
TOKEN = "YOUR DISCORD TOKEN HERE"  # 自分のアクセストークンと置換

# Botの大元となるオブジェクトを生成する
bot = discord.Bot(
        intents=discord.Intents.all(),  # 全てのインテンツを利用できるようにする
        activity=discord.Game("集まったミーム漁り"),  # "〇〇をプレイ中"の"〇〇"を設定,
)


# ボットが起動したときに実行されるイベント
@bot.event
async def on_ready():
    #グローバル変数{select_playlist}を定義
    global select_playlist
    select_playlist = None
    # データベースに接続してコネクションとカーソルをグローバル変数に格納する
    global conn, cur
    conn, cur = connect_db()
    print(f'{bot.user.name} has connected to Discord!')
    print("select_pを忘れずに！")
    
@bot.event
async def setup_hook(self):
    await self.tree.sync()
    

# youtubeの動画idを抽出する正規表現
youtube_pattern = re.compile(r"(?:https?://)?(?:www\.)?(?:youtube\.com/(?:watch\?v=|shorts/)|youtu\.be/)([a-zA-Z0-9_-]+)")

# ISO 8601形式の文字列を秒数に変換する関数
def convert_to_seconds(iso_string):
    # 文字列から"P"と"T"を除去
    iso_string = iso_string.replace("P", "").replace("T", "")
    # 時間、分、秒の単位を表す文字をキーとして辞書を作成
    units = {"H": 3600, "M": 60, "S": 1}
    # 秒数を初期化
    seconds = 0
    # 辞書のキーに対応する単位が文字列に含まれているかチェック
    for key in units:
        # 単位が含まれている場合
        if key in iso_string:
            # 単位の前にある数字を取得
            num = int(iso_string.split(key)[0])
            # 秒数に数字と単位の積を加算
            seconds += num * units[key]
            # 文字列から数字と単位を除去
            iso_string = iso_string.replace(str(num) + key, "")
    # 秒数を返す
    return seconds

# メッセージ受信時に動作する処理
@bot.event
async def on_message(message):
    # メッセージ送信者がBotだった場合は無視する
    if message.author.bot:
        return
    
    # 特定のチャンネルIDだった場合は無視する
    ignore_channels = [1159101801786781776,1069634960941666426,1116691516350541856,1142058797284724737,1140287772704382976,1150074574596218962] # 無視するチャンネルIDのリスト
    if message.channel.id in ignore_channels:
        return
    
    # メッセージの内容からyoutubeの動画idを探す
    match = youtube_pattern.search(message.content)
    if match:
        # 動画idを変数に格納する
        video_id_m = match.group(1)
        
        # SQL文を作成
        sql = "SELECT * FROM video_info_table WHERE video_id = %s"

        # SQL文を実行して結果を取得
        cur.execute(sql, (video_id_m,))
        result = cur.fetchone()

        # 追加済み出会った場合(検索結果がNone出ない場合)
        if result is not None:
           #返信の候補をリストに格納
            duplicate_replys = ["おいジョージ、前のと被ってんぞ" , "もうあるんだな、これが。" , "DIO様より「関係ない。消せ」" , "(動画の)用意はとっくにできてるぜ？" , "神は言っている...これはもう見たと。" , "オラこれもう見てっぞ！"]
            duplicate_reply = random.choice(duplicate_replys) # リストからランダムに一つ選ぶ
           # 送ったユーザーにリプライする
            await message.reply(f"{duplicate_reply}")
        elif select_playlist is None:
            await message.reply("プレイリストが未選択です！")
            return
        elif select_playlist is not None:
            # youtube data apiで動画情報を取得（try-except文でエラー処理）
            try:
                youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, credentials=credentials)
                # youtube data apiで動画情報を取得
                video_info = youtube.videos().list(
                part="snippet,contentDetails",
                id=video_id_m
                ).execute()
            except BrokenPipeError as e:
                # エラーが発生した場合は再接続やリトライを行う（再試行回数や間隔は適宜調整）
                print(f"BrokenPipeError: {e}")
                print("Trying to reconnect...")
                # 認証情報をリフレッシュする
                credentials.refresh(Request())
                # youtubeオブジェクトを再作成する
                youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, credentials=credentials)
                # リクエストを再送する（最大3回まで）
                retry_count = 0
                while retry_count < 3:
                    try:
                        youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, credentials=credentials)
                        # リクエスト前に少し待つ
                        time.sleep(1)
                        # youtube data apiで動画情報を取得
                        video_info = youtube.videos().list(
                        part="snippet,contentDetails",
                        id=video_id_m
                        ).execute()
                        # リクエストが成功したらループを抜ける
                        break
                    except BrokenPipeError as e:
                        # リクエストが失敗したら再試行回数を増やす
                        print(f"BrokenPipeError: {e}")
                        print("Trying to retry...")
                        retry_count += 1
                # 最大試行回数を超えたらエラーを通知する
                if retry_count == 3:
                    print("Failed to reconnect or retry.")
                    await message.channel.send("YouTube Data APIとの通信に失敗しました。しばらくしてからもう一度お試しください。")
                    return
                
            # 動画情報から必要なデータを抽出
            video_title = video_info["items"][0]["snippet"]["title"]
            video_link = "https://www.youtube.com/watch?v=" + video_id_m
            # video_lengthを秒数に変換する関数を呼び出す
            video_length = convert_to_seconds(video_info["items"][0]["contentDetails"]["duration"])
            # added_timeをmessageオブジェクトから取得し、ISO 8601形式に変換する
            added_time = message.created_at.isoformat()
            added_channel = message.channel.name
            server_id_in = message.guild.id
                
            # DBに動画情報を挿入するSQL文を作成
            sql_video = """
            INSERT INTO video_info_table (video_id, video_title, video_link, video_length, added_time, added_channel, server_id_in)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING record_id;
            """
            # DBに動画情報を挿入し、record_idを取得
            cur.execute(sql_video, (video_id_m, video_title, video_link, video_length, added_time, added_channel, server_id_in))
            conn.commit()
            video_record_id = cur.fetchone()[0]

            # DBからプレイリスト情報を取得するSQL文を作成
            sql_playlist = """
                SELECT record_id FROM playlist_info_table WHERE playlist_id = %s;
            """
            # DBからプレイリスト情報を取得し、record_idを取得
            cur.execute(sql_playlist, (select_playlist,))
            playlist_record_id = cur.fetchone()[0]

            # DBにプレイリストと動画の関係を挿入するSQL文を作成
            sql_relation = """
                INSERT INTO playlist_video_relation_table (playlist_record_id, video_record_id)
                VALUES (%s, %s);
            """
            # DBにプレイリストと動画の関係を挿入
            cur.execute(sql_relation, (playlist_record_id, video_record_id))
            conn.commit()

            # youtube data apiでプレイリストに動画を追加するリクエストを作成（try-except文でエラー処理）
            try:
                youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, credentials=credentials)
                request = youtube.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": select_playlist,
                        "resourceId": {
                            "kind": "youtube#video",
                            "videoId": video_id_m
                        }
                    }
                   }
                )
                # youtube data apiでプレイリストに動画を追加するリクエストを実行
                response = request.execute()
            except BrokenPipeError as e:
                # エラーが発生した場合は再接続やリトライを行う（再試行回数や間隔は適宜調整）
                print(f"BrokenPipeError: {e}")
                print("Trying to reconnect...")
                # 認証情報をリフレッシュする
                credentials.refresh(Request())
                # youtubeオブジェクトを再作成する
                youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, credentials=credentials)
                # リクエストを再送する（最大3回まで）
                retry_count = 0
                while retry_count < 3:
                    try:
                        youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, credentials=credentials)
                        # リクエスト前に少し待つ
                        time.sleep(1)
                        request = youtube.playlistItems().insert(
                            part="snippet",
                            body={
                                "snippet": {
                                    "playlistId": select_playlist,
                                    "resourceId": {
                                        "kind": "youtube#video",
                                        "videoId": video_id_m
                                }
                            }
                           }
                        )
                        # youtube data apiでプレイリストに動画を追加するリクエストを実行
                        response = request.execute()
                        # リクエストが成功したらループを抜ける
                        break
                    except BrokenPipeError as e:
                        # リクエストが失敗したら再試行回数を増やす
                        print(f"BrokenPipeError: {e}")
                        print("Trying to retry...")
                        retry_count += 1
                        # 最大試行回数を超えたらエラーを通知する
                if retry_count == 3:
                    print("Failed to reconnect or retry.")
                    await message.channel.send("YouTube Data APIとの通信に失敗しました。しばらくしてからもう一度お試しください。")
                    return

            # メッセージ送信者に返信するメッセージを作成
            added_message = f"「{playlist_name_m}」へ「{video_title}」の追加が完了しました。"
            
            # サーバーidによって、送信先のチャンネルを変える
            if server_id_in == 1116691515666878555:
                channel = bot.get_channel(1150074574596218962)
            elif server_id_in == 1069634960396394516:
                channel = bot.get_channel(1159101763857694720)
            else:
                # その他のサーバーidの場合はデフォルトのチャンネルidを設定
                channel = bot.get_channel(0)
                
            # 対象チャンネルに返信する
            await channel.send(added_message)


        
    elif message.content == 'hello':
        # メッセージが"hello"だった場合、"Hello!"と返信する
        await message.reply("Hello!")
    else:
        # youtubeの動画idも"hello"も見つからなかった場合は何もしない
       return



# helloコマンドを実装
@bot.command(name="hello", description="Hello, worldと返す。ただそれだけ")
async def hello(ctx: discord.ApplicationContext):
        await ctx.respond("Hello, world!")
        


# select_pコマンドを実装
@bot.command(name="select_p", description="【管理者】データベース内にあるプレイリストを選択します")
@commands.has_permissions(administrator=True) # 管理者権限を持っているかどうかをチェックするデコレータ
async def select_p(ctx: discord.ApplicationContext, playlist_name: str): # デフォルト値をNoneにする
    
    #グローバル変数にプレイリスト名を格納
    global playlist_name_m
    playlist_name_m = playlist_name
    
    # プレイリスト名が空でないかチェックする
    if not playlist_name:
        await ctx.respond("プレイリスト名を入力してください。") # respond() を使う
        return
    
    # プレイリスト名が"list"だった場合は、以下の処理を行う
    if playlist_name == "list":

        # SQL文を作成
        sql = "SELECT playlist_name, playlist_link FROM playlist_info_table"

        # SQL文を実行して結果を取得
        cur.execute(sql)
        result = cur.fetchall()

        # 結果が空でなければ、プレイリスト名とリンクの表を作成してメッセージを表示
        if result:
            # 表のヘッダーを作成
            header = "| プレイリスト名 | リンク |\n"
            # 表の内容を作成
            content = ""
            for row in result:
                content += f"| {row[0]} | {row[1]} |\n" # リンクはそのまま表示する
            # 表の全体を作成
            table = header + content
            # 送ったユーザーにリプライする
            await ctx.respond(f"以下はデータベースに登録されているプレイリストの一覧です。\n{table}")
        else:
            # 結果が空ならば、データベースにプレイリストが存在しないというメッセージを表示
            await ctx.respond("データベースにプレイリストが存在しません。")
        return
    
    # プレイリスト名が"list"以外だった場合は、以下の処理を続ける

    # SQL文を作成
    sql = "SELECT playlist_id FROM playlist_info_table WHERE playlist_name = %s"

    # SQL文を実行して結果を取得
    cur.execute(sql, (playlist_name,))
    result = cur.fetchone()

    # 結果がNoneでなければ、プレイリストidを変数に格納してメッセージを表示
    if result is not None:
        #グローバル変数{select_playlist}を定義
        global select_playlist
        # プレイリストidをグローバル変数に格納する
        select_playlist = result[0] # タプルの最初の要素を取り出す
        # 送ったユーザーにリプライする
        await ctx.respond(f"プレイリスト「{playlist_name}」を選択しました。ID:{select_playlist}")
    else:
        # 結果がNoneならば、プレイリスト名が存在しないというメッセージを表示
        await ctx.respond(f"プレイリスト「{playlist_name}」は存在しません。")
        
# list_pコマンドを実装
@bot.command(name="list_p", description="データベース内にあるプレイリストを一覧表示します")
async def list_p(ctx: discord.ApplicationContext): # デフォルト値をNoneにする

        # SQL文を作成
        sql = "SELECT playlist_name, playlist_link FROM playlist_info_table"

        # SQL文を実行して結果を取得
        cur.execute(sql)
        result = cur.fetchall()

        # 結果が空でなければ、プレイリスト名とリンクの表を作成してメッセージを表示
        if result:
            # 表のヘッダーを作成
            header = "| プレイリスト名 | リンク |\n"
            # 表の内容を作成
            content = ""
            for row in result:
                content += f"| {row[0]} | {row[1]} |\n" # リンクはそのまま表示する
            # 表の全体を作成
            table = header + content
            # 送ったユーザーにリプライする
            await ctx.respond(f"以下はデータベースに登録されているプレイリストの一覧です。\n{table}")
        else:
            # 結果が空ならば、データベースにプレイリストが存在しないというメッセージを表示
            await ctx.respond("データベースにプレイリストが存在しません。")
        return


# VersionPクラスのインスタンスを作成して、Botオブジェクトに登録
bot.add_cog(VersionP(bot))


# Botを起動
bot.run(TOKEN)
