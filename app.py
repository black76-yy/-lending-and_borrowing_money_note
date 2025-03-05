from flask import Flask,redirect, url_for, session,request,render_template, Response
from authlib.integrations.flask_client import OAuth
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import func
from sqlalchemy.orm import Session
import os,datetime
import logging,requests
from math import ceil
from flask_paginate import Pagination, get_page_parameter

logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__)
# ページあたりの項目数
ITEMS_PER_PAGE = 5



#DBファイル設定
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['GOOGLE_CLIENT_ID'] = '50368705725-a48qvtmcmfa6kcdbfmb8kob71e48n5v0.apps.googleusercontent.com'
app.config['GOOGLE_CLIENT_SECRET'] = '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'
base_dir = os.path.dirname(__file__)
database = "sqlite:///" + os.path.join(base_dir, 'cash.sqlite')
app.config['SQLALCHEMY_DATABASE_URI'] = database
app.config['SQALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
#Session = sessionmaker(bind=db.engine)

Migrate(app, db)

# OAuthの設定
oauth = OAuth(app)

google_discovery_url = "https://accounts.google.com/.well-known/openid-configuration"


google = oauth.register(
    name='google',
    client_id=app.config['GOOGLE_CLIENT_ID'],
    client_secret=app.config['GOOGLE_CLIENT_SECRET'],
    server_metadata_url=google_discovery_url,
    client_kwargs={'scope': 'openid email profile'},
)

class User(db.Model):
    __tablename__ = "user"

    user_id = db.Column(db.Integer, primary_key=True, nullable=False,autoincrement=True)
    email = db.Column(db.String, unique=True, nullable=False)
    name = db.Column(db.String)
    picture = db.Column(db.String)

    party = db.relationship("Party",backref = "user", cascade='all, delete-orphan')
    return_money = db.relationship("Return_money",backref = "user", cascade='all, delete-orphan')
    returned_money = db.relationship("Returned_money",backref = "user", cascade='all, delete-orphan')
    lend_money = db.relationship("Lend_money",backref = "user", cascade='all, delete-orphan')
    borrow_money = db.relationship("Borrow_money",backref = "user", cascade='all, delete-orphan')

class Party(db.Model):
    __tablename__ = "party"

    party_id = db.Column(db.Integer, primary_key=True, nullable=False,autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.user_id"), nullable=False)
    last_name = db.Column(db.String)
    first_name = db.Column(db.String)
    relation = db.Column(db.String)
    return_money = db.Column(db.Integer)
    returned_money = db.Column(db.Integer)

    return_money = db.relationship("Return_money",backref = "party", cascade='all, delete-orphan')
    returned_money = db.relationship("Returned_money",backref = "party", cascade='all, delete-orphan')
    lend_money = db.relationship("Lend_money",backref = "party", cascade='all, delete-orphan')
    borrow_money = db.relationship("Borrow_money",backref = "party", cascade='all, delete-orphan')

class Return_money(db.Model):
    __tablename__ = "return_money"

    return_id = db.Column(db.Integer, primary_key=True, nullable=False,autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.user_id"), nullable=False, unique=False)
    party_id = db.Column(db.Integer, db.ForeignKey("party.party_id"), nullable=False, unique=False)
    amount = db.Column(db.Integer, nullable=False,default=0)
    type = db.Column(db.String)
    created_at = db.Column(db.DateTime, nullable=False)

class Returned_money(db.Model):
    __tablename__ = "returned_money"

    returned_id = db.Column(db.Integer, primary_key=True, nullable=False,autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.user_id"), nullable=False, unique=False)
    party_id = db.Column(db.Integer, db.ForeignKey("party.party_id"), nullable=False, unique=False)
    amount = db.Column(db.Integer, nullable=False,default=0)
    type = db.Column(db.String)
    created_at = db.Column(db.DateTime, nullable=False)

class Lend_money(db.Model):
    __tablename__ = "lend_money"

    lend_id = db.Column(db.Integer, primary_key=True, nullable=False,autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.user_id"), nullable=False, unique=False)
    party_id = db.Column(db.Integer, db.ForeignKey("party.party_id"), nullable=False, unique=False)
    amount = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String)
    created_at = db.Column(db.DateTime, nullable=False)

class Borrow_money(db.Model):
    __tablename__ = "borrow_money"

    borrow_id = db.Column(db.Integer, primary_key=True, nullable=False,autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.user_id"), nullable=False, unique=False)
    party_id = db.Column(db.Integer, db.ForeignKey("party.party_id"), nullable=False, unique=False)
    amount = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String)
    created_at = db.Column(db.DateTime, nullable=False)


#google Oauth2認証
#====================================================================================================
@app.route('/')
def index():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        #ここでtop_pageに飛ばす
        return redirect(url_for("top_page"))
    return render_template("index.html")

@app.route('/login')
def login():
    redirect_uri = url_for('authorize', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@app.route('/authorize')
def authorize():
    token = oauth.google.authorize_access_token()
    resp = oauth.google.get('https://www.googleapis.com/oauth2/v3/userinfo')
    user_info = resp.json()
    
    user_data = {
        'email': user_info['email'],
        'name': user_info['name'],
        'picture': user_info['picture'],
    }
    
    user = User.query.filter_by(email=user_data['email']).first()
    if user is None:
        user = User(email=user_data['email'], name=user_data['name'], picture=user_data['picture'])
        db.session.add(user)
        db.session.commit()
    
    session['user_id'] = user.user_id
    return redirect('/')

@app.route('/logout')
def logout():
    for key in list(session.keys()):
        session.pop(key)
    return redirect('/')
#====================================================================================================
@app.route('/payment')
def payment():
    # ここで、実際のStripeの課金ページにリダイレクトします
    return redirect("https://buy.stripe.com/test_00geYkbuD78nebu6oo")

"""
初めに表示されるメイン画面

POST：
    新しい貸し借りデータの新規登録

GET：
    party別の最終的にいくら返す・もらうのかを表示する
    ・貸し借り新規登録フォームで存在するデータを選択肢に表示させるため、
    そのデータも別変数で送信している
"""
@app.route("/toppage", methods = ["GET","POST"])
def top_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    
    if request.method == 'POST':
        add_user_id = user_id
        add_party_id = request.form.get("party_id")
        add_amount = request.form.get("amount")
        type_select = request.form['type_select']
        type_input = request.form['type_input']
        type_value = type_select if type_select else type_input
        add_created_at = datetime.datetime.today()
        if request.form.get("lend_or_borrow")=="borrow":
            new_money = Borrow_money(user_id=add_user_id,
                            party_id=add_party_id,
                            amount=add_amount,
                            type=type_value,
                            created_at=add_created_at)
            db.session.add(new_money)
            db.session.commit()

        elif request.form.get("lend_or_borrow")=="lend":
            new_money = Lend_money(user_id=add_user_id,
                            party_id=add_party_id,
                            amount=add_amount,
                            type=type_value,
                            created_at=add_created_at)
            db.session.add(new_money)
            db.session.commit()

        return redirect(url_for("top_page"))

    #ここからがgetメソッド処理
    views = []
    partys = Party.query.filter(Party.user_id == user_id).with_entities(Party.party_id).all()


    partys = [pid[0] for pid in partys]




    for party_id in partys:
        subquery_return = db.session.query(
            Return_money.party_id,
            func.sum(Return_money.amount).label("total_return")
        ).filter(Return_money.party_id == party_id).group_by(Return_money.party_id).subquery()

        subquery_returned = db.session.query(
            Returned_money.party_id,
            func.sum(Returned_money.amount).label("total_returned")
        ).filter(Returned_money.party_id == party_id).group_by(Returned_money.party_id).subquery()

        subquery_borrowed = db.session.query(
            Borrow_money.party_id,
            func.sum(Borrow_money.amount).label("total_borrowed")
        ).filter(Borrow_money.party_id == party_id).group_by(Borrow_money.party_id).subquery()

        subquery_lent = db.session.query(
            Lend_money.party_id,
            func.sum(Lend_money.amount).label("total_lend")
        ).filter(Lend_money.party_id == party_id).group_by(Lend_money.party_id).subquery()

        view_info = db.session.query(
            Party.party_id,
            Party.first_name,
            Party.last_name,
            func.coalesce(subquery_borrowed.c.total_borrowed, 0).label("total_borrowed"),
            func.coalesce(subquery_lent.c.total_lend, 0).label("total_lend"),
            func.coalesce(subquery_return.c.total_return, 0).label("total_return"),
            func.coalesce(subquery_returned.c.total_returned, 0).label("total_returned")
        ).outerjoin(subquery_return, subquery_return.c.party_id == Party.party_id)\
        .outerjoin(subquery_returned, subquery_returned.c.party_id == Party.party_id)\
        .outerjoin(subquery_borrowed, subquery_borrowed.c.party_id == Party.party_id)\
        .outerjoin(subquery_lent, subquery_lent.c.party_id == Party.party_id)\
        .filter(Party.party_id == party_id)\
        .first()

        if view_info:
            total_borrowed = view_info.total_borrowed if view_info.total_borrowed is not None else 0
            total_lend = view_info.total_lend if view_info.total_lend is not None else 0
            total_return = view_info.total_return if view_info.total_return is not None else 0
            total_returned = view_info.total_returned if view_info.total_returned is not None else 0

            money = total_borrowed - total_lend - total_return + total_returned


            result = {
                "party_id": view_info.party_id,
                "first_name": view_info.first_name,
                "last_name": view_info.last_name,
                "money": money
            }
        else:
            result = {
                "party_id": None,
                "first_name": None,
                "last_name": None,
                "money": None
            }
        
        if money != 0:
            views.append(result)



    # 相手方一覧のデータ
    party_list = Party.query.filter(Party.user_id == user_id).with_entities(Party.first_name, Party.last_name, Party.party_id).all()

    #科目一覧のデータ
    lend_money_types = Lend_money.query.with_entities(Lend_money.type).distinct().all()
    borrow_money_types = Borrow_money.query.with_entities(Borrow_money.type).distinct().all()
    return_money_types = Return_money.query.with_entities(Return_money.type).distinct().all()
    returned_money_types = Returned_money.query.with_entities(Returned_money.type).distinct().all()

    # 重複しないようにタイプを統合し、Noneを取り除く
    type_list = list(set([t[0] for t in lend_money_types if t[0] is not None] +
                         [t[0] for t in borrow_money_types if t[0] is not None] +
                         [t[0] for t in return_money_types if t[0] is not None] +
                         [t[0] for t in returned_money_types if t[0] is not None]))
    
    page = request.args.get(get_page_parameter(), type=int, default=1)
    rows = views[(page - 1) * ITEMS_PER_PAGE: page * ITEMS_PER_PAGE]
    pagination = Pagination(page=page, total=len(views), per_page=ITEMS_PER_PAGE, css_framework='bootstrap5')
    return render_template("top_page.html", party_list=party_list,type_list=type_list, views=rows, pagination=pagination)

@app.route("/update/returned", methods = ["GET","POST"])
def upgrade_party_returned():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        user_id = session['user_id']
        party_id = request.form.get("party_id")
        db_session = Session(db.engine)
        returned_money = request.form.get("returned_money")
        type_select = request.form['type_select']
        type_input = request.form['type_input']
        type_value = type_select if type_select else type_input
        created_at = datetime.datetime.today()
        new_returned = Returned_money(user_id=user_id,
                                      party_id=party_id,
                                      amount=returned_money,
                                      type=type_value,
                                      created_at=created_at)

        db_session.add(new_returned)
        db_session.commit()
        db_session.close()

        return redirect(url_for("top_page"))
    print("失敗")
    return redirect(url_for("top_page"))


@app.route("/deleat/return", methods = ["POST"])
def deleat_return():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return_id = request.form.get("return_id")
    party_id = request.form.get("party_id")
    db_session = Session(db.engine)
    return_data = db_session.get(Return_money, return_id)

    db_session.delete(return_data)
    db_session.commit()
    db_session.close()

    # requests.Sessionを使用してセッション情報を共有
    with requests.Session() as s:
        post_url = url_for('borrow_detail_page', _external=True)
        post_data = {'party_id': party_id}

        # FlaskのセッションIDをrequestsセッションに追加
        cookies = {'session': request.cookies.get('session')}
        response = s.post(post_url, data=post_data, cookies=cookies)

    # POSTリクエストのレスポンスをそのまま返す
    if response.status_code == 200:
        return Response(response.text, status=response.status_code, content_type=response.headers['Content-Type'])
    else:
        # エラーが発生した場合の処理
        return Response(f"Error occurred: {response.text}", status=response.status_code, content_type="text/plain")
    
@app.route("/deleat/returned", methods = ["POST"])
def deleat_returned():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    returned_id = request.form.get("return_id")
    party_id = request.form.get("party_id")
    db_session = Session(db.engine)
    returned_data = db_session.get(Returned_money, returned_id)

    db_session.delete(returned_data)
    db_session.commit()
    db_session.close()

    # requests.Sessionを使用してセッション情報を共有
    with requests.Session() as s:
        post_url = url_for('lend_detail_page', _external=True)
        post_data = {'party_id': party_id}

        # FlaskのセッションIDをrequestsセッションに追加
        cookies = {'session': request.cookies.get('session')}
        response = s.post(post_url, data=post_data, cookies=cookies)

    # POSTリクエストのレスポンスをそのまま返す
    if response.status_code == 200:
        return Response(response.text, status=response.status_code, content_type=response.headers['Content-Type'])
    else:
        # エラーが発生した場合の処理
        return Response(f"Error occurred: {response.text}", status=response.status_code, content_type="text/plain")

@app.route("/update/return", methods=["GET", "POST"])
def upgrade_party_return():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    

    
    if request.method == 'POST':
        user_id = session['user_id']
        party_id = request.form.get("party_id")
        db_session = Session(db.engine)
        return_money = request.form.get("return_money")
        type_select = request.form['type_select']
        type_input = request.form['type_input']
        type_value = type_select if type_select else type_input
        created_at = datetime.datetime.today()
        new_return = Return_money(user_id=user_id,
                                      party_id=party_id,
                                      amount=return_money,
                                      type=type_value,
                                      created_at=created_at)

        db_session.add(new_return)
        db_session.commit()
        db_session.close()

        return redirect(url_for("top_page"))
    print("失敗")
    return redirect(url_for("top_page"))


"""
partyページを表示する
POST:
    新規作成されたpartyを追加する

GET:
    party一覧を表示する
    ボタンからpartyの削除を実行できる
"""
@app.route("/add/party", methods = ["GET","POST"])
def party_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    if request.method == 'POST':
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        relation = request.form.get("relation")
        new_party = Party(user_id=user_id,first_name=first_name,last_name=last_name,relation=relation)

        db.session.add(new_party)
        db.session.commit()

        return redirect(url_for("party_page"))
    party_list = Party.query.\
                    filter(Party.user_id==user_id).\
                    with_entities(Party.party_id,
                                  Party.first_name,
                                  Party.last_name,
                                  Party.relation).\
                    all()
    
    page = request.args.get(get_page_parameter(), type=int, default=1)
    rows = party_list[(page - 1) * ITEMS_PER_PAGE: page * ITEMS_PER_PAGE]
    pagination = Pagination(page=page, total=len(party_list), per_page=ITEMS_PER_PAGE, css_framework='bootstrap5')
    print(ITEMS_PER_PAGE)
    return render_template("party_page.html", party_list=rows, pagination=pagination)


"""
party削除を実行する関数

削除を完了させたらparty_page()へリダイレクトする
"""
@app.route("/party/deleat", methods = ["GET","POST"])
def party_deleat():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    party_id = request.form.get("party_id")
    db_session = Session(db.engine)
    party = db_session.get(Party, party_id)
    if party is None:
        return redirect(url_for("party_page"))


    print(party)

    db_session.delete(party)
    db_session.commit()
    db_session.close()

    return redirect(url_for("party_page")) 


"""
借りた金額をpaty別で表示する

表示される金額はpartyごとの合計金額

ボタンを押すとlend_detail_page()にリダイレクトする
"""
@app.route("/lend")
def lend_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    views = []
    partys = Party.query.filter(Party.user_id == user_id).with_entities(Party.party_id).all()
    partys = [pid[0] for pid in partys]


    for party_id in partys:

        subquery_returned = db.session.query(
            Returned_money.party_id,
            func.sum(Returned_money.amount).label("total_returned")
        ).filter(Returned_money.party_id == party_id).group_by(Returned_money.party_id).subquery()
          
        view_info = db.session.query(
            Party.party_id,
            Party.first_name,
            Party.last_name,
            func.coalesce(subquery_returned.c.total_returned, 0).label("total_returned"))\
        .filter(Party.party_id == party_id)\
        .outerjoin(subquery_returned, subquery_returned.c.party_id == Party.party_id)\
        .group_by(Party.first_name).first()



        if view_info:

            total_returned = view_info.total_returned if view_info.total_returned is not None else 0
            result = {
                "party_id": view_info.party_id,
                "first_name": view_info.first_name,
                "last_name": view_info.last_name,
                "money":total_returned
            }
            

        else:
            result = {
                "party_id": None,
                "first_name": None,
                "last_name": None,
                "money": None
            }

        views.append(result)

    
    page = request.args.get(get_page_parameter(), type=int, default=1)
    rows = views[(page - 1) * ITEMS_PER_PAGE: page * ITEMS_PER_PAGE]
    pagination = Pagination(page=page, total=len(views), per_page=ITEMS_PER_PAGE, css_framework='bootstrap5')

    return render_template("lend_page.html", views=rows,pagination=pagination)

"""
    貸した金額をpaty別で表示する

表示される金額はpartyごとの合計金額

ボタンを押すとlend_detail_page()にリダイレクトする
"""
@app.route("/borrow")
def borrow_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    views = []
    partys = Party.query.filter(Party.user_id == user_id).with_entities(Party.party_id).all()
    partys = [pid[0] for pid in partys]



    for party_id in partys:

        subquery_return = db.session.query(
            Return_money.party_id,
            func.sum(Return_money.amount).label("total_return")
        ).filter(Return_money.party_id == party_id).group_by(Return_money.party_id).subquery()
          
        view_info = db.session.query(
            Party.party_id,
            Party.first_name,
            Party.last_name,
            func.coalesce(subquery_return.c.total_return, 0).label("total_return"))\
        .filter(Party.party_id == party_id)\
        .outerjoin(subquery_return, subquery_return.c.party_id == Party.party_id)\
        .group_by(Party.first_name).first()

        


        if view_info:

            total_return = view_info.total_return if view_info.total_return is not None else 0
            result = {
                "party_id": view_info.party_id,
                "first_name": view_info.first_name,
                "last_name": view_info.last_name,
                "money":total_return
            }
            

        else:
            result = {
                "party_id": None,
                "first_name": None,
                "last_name": None,
                "money": None
            }

        views.append(result)

    page = request.args.get(get_page_parameter(), type=int, default=1)
    rows = views[(page - 1) * ITEMS_PER_PAGE: page * ITEMS_PER_PAGE]
    pagination = Pagination(page=page, total=len(views), per_page=ITEMS_PER_PAGE, css_framework='bootstrap5')

    return render_template("borrow_page.html", views=rows,pagination=pagination)


@app.route("/lend/detail", methods = ["GET","POST"])
def lend_detail_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    party_id = request.form.get("party_id")
    page = request.args.get(get_page_parameter(), type=int, default=1)
    if request.method == 'POST':
        lend_detail = Lend_money.query.\
                        filter(Lend_money.user_id==user_id,
                            Lend_money.party_id==request.form.get("party_id")).\
                        join(Party, Lend_money.party_id == Party.party_id).\
                        with_entities(Party.first_name,
                                    Party.last_name,
                                    Party.party_id,
                                    Lend_money.amount,
                                    Lend_money.type,
                                    Lend_money.created_at,
                                    Lend_money.lend_id).\
                        all()
        
        subquery_returned = db.session.query(
            Returned_money.party_id,
            Returned_money.amount,
            Returned_money.type,
            Returned_money.created_at,
            Returned_money.returned_id
        ).filter(Returned_money.party_id == party_id).subquery()

        subquery = db.session.query(
            Returned_money.party_id,
        ).filter(Returned_money.party_id == party_id).group_by(Returned_money.party_id).first()
        if subquery:  
            view_info = db.session.query(
                Party.party_id,
                Party.first_name,
                Party.last_name,
                func.coalesce(subquery_returned.c.amount, 0).label("amount"),
                subquery_returned.c.type,
                subquery_returned.c.created_at,
                subquery_returned.c.returned_id)\
            .filter(Party.party_id == party_id)\
            .outerjoin(subquery_returned, subquery_returned.c.party_id == Party.party_id)\
            .all()

            row = view_info[(page - 1) * ITEMS_PER_PAGE: page * ITEMS_PER_PAGE]
        else:
            row = None
    
    rows = lend_detail[(page - 1) * ITEMS_PER_PAGE: page * ITEMS_PER_PAGE]
    pagination = Pagination(page=page, total=len(lend_detail), per_page=ITEMS_PER_PAGE, css_framework='bootstrap5')
    return render_template("lend_detail_page.html",lend_detail=rows,view_info=row,pagination=pagination)
    
@app.route("/borrow/detail", methods = ["GET","POST"])
def borrow_detail_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    party_id = request.form.get("party_id")
    page = request.args.get(get_page_parameter(), type=int, default=1)
    borrow_detail = Borrow_money.query.\
        filter(Borrow_money.user_id == user_id,
                Borrow_money.party_id == party_id).\
        join(Party, Borrow_money.party_id == Party.party_id).\
        with_entities(Party.first_name,
                        Party.last_name,
                        Party.party_id,
                        Borrow_money.amount,
                        Borrow_money.type,
                        Borrow_money.created_at,
                        Borrow_money.borrow_id).\
        all()
    
    subquery_return = db.session.query(
        Return_money.party_id,
        Return_money.amount,
        Return_money.type,
        Return_money.created_at,
        Return_money.return_id
    ).filter(Return_money.party_id == party_id).subquery()

    subquery = db.session.query(
        Return_money.party_id,
    ).filter(Return_money.party_id == party_id).group_by(Return_money.party_id).first()

    if subquery:
        
        view_info = db.session.query(
            Party.party_id,
            Party.first_name,
            Party.last_name,
            func.coalesce(subquery_return.c.amount, 0).label("amount"),
            subquery_return.c.type,
            subquery_return.c.created_at,
            subquery_return.c.return_id)\
        .filter(Party.party_id == party_id)\
        .outerjoin(subquery_return, subquery_return.c.party_id == Party.party_id)\
        .all()

        row = view_info[(page - 1) * ITEMS_PER_PAGE: page * ITEMS_PER_PAGE]

    else:
        row = None

    
    rows = borrow_detail[(page - 1) * ITEMS_PER_PAGE: page * ITEMS_PER_PAGE]
    pagination = Pagination(page=page, total=len(borrow_detail), per_page=ITEMS_PER_PAGE, css_framework='bootstrap5')
    return render_template("borrow_detail_page.html",borrow_detail=rows,view_info=row,pagination=pagination)


@app.route("/lend/deleat", methods = ["POST"])
def deleat_lend():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']

    party_id = request.form.get("party_id")
    lend_id = request.form.get("lend_id")
    db_session = Session(db.engine)
    lend = db_session.query(Lend_money).filter(Lend_money.lend_id == lend_id).first()


    db_session.delete(lend)
    db_session.commit()
    db_session.close()

    # requests.Sessionを使用してセッション情報を共有
    with requests.Session() as s:
        post_url = url_for('lend_detail_page', _external=True)
        post_data = {'party_id': party_id}

        # FlaskのセッションIDをrequestsセッションに追加
        cookies = {'session': request.cookies.get('session')}
        response = s.post(post_url, data=post_data, cookies=cookies)
        
    # POSTリクエストのレスポンスをそのまま返す
    if response.status_code == 200:
        return Response(response.text, status=response.status_code, content_type=response.headers['Content-Type'])
    else:
        # エラーが発生した場合の処理
        return Response(f"Error occurred: {response.text}", status=response.status_code, content_type="text/plain")

        



@app.route("/borrow/deleat", methods = ["POST"])
def deleat_borrow():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']

    party_id = request.form.get("party_id")
    borrow_id = request.form.get("borrow_id")
    db_session = Session(db.engine)
    borrow = db_session.query(Borrow_money).filter(Borrow_money.borrow_id == borrow_id).first()
    print(borrow)

    db_session.delete(borrow)
    db_session.commit()
    db_session.close()

    # requests.Sessionを使用してセッション情報を共有
    with requests.Session() as s:
        post_url = url_for('borrow_detail_page', _external=True)
        post_data = {'party_id': party_id}

        # FlaskのセッションIDをrequestsセッションに追加
        cookies = {'session': request.cookies.get('session')}
        response = s.post(post_url, data=post_data, cookies=cookies)
        
    # POSTリクエストのレスポンスをそのまま返す
    if response.status_code == 200:
        return Response(response.text, status=response.status_code, content_type=response.headers['Content-Type'])
    else:
        # エラーが発生した場合の処理
        return Response(f"Error occurred: {response.text}", status=response.status_code, content_type="text/plain")
        


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')