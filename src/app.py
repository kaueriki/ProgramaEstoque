from flask import Flask, render_template, request, redirect, url_for, session, flash
from sqlalchemy.orm import sessionmaker
from models import engine, Usuario, Material

app = Flask(__name__)
app.secret_key = "supersecret"

Session = sessionmaker(bind=engine)
db_session = Session()


@app.route("/")
def index():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():
    operador = request.form["operador"]
    senha = request.form["senha"]

    print(f"Tentando login com -> Operador: {operador}, Senha: {senha}")

    user = db_session.query(Usuario).filter_by(nome=operador, senha=senha).first()
    print("Resultado query:", user)

    if user:
        session["usuario_id"] = user.id
        print("Login OK, redirecionando...")
        return redirect(url_for("novo_material"))
    else:
        flash("Usuário ou senha inválidos!", "error")
        print("Login falhou")
        return redirect(url_for("index"))


@app.route("/materiais/novo", methods=["GET", "POST"])
def novo_material():
    if "usuario_id" not in session:
        flash("Você precisa estar logado!", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        nome = request.form["nome"]
        qtd = request.form["quantidade"]
        novo = Material(nome=nome, quantidade=qtd)
        db_session.add(novo)
        db_session.commit()
        return redirect(url_for("listar_materiais"))
    return render_template("novo_material.html")


@app.route("/materiais")
def listar_materiais():
    if "usuario_id" not in session:
        flash("Você precisa estar logado!", "error")
        return redirect(url_for("index"))

    materiais = db_session.query(Material).all()
    return render_template("materiais.html", materiais=materiais)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
