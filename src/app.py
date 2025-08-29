from flask import Flask, render_template, request, redirect, url_for
from sqlalchemy.orm import sessionmaker
from models import engine, Usuario, Cliente, Material, Movimentacao

app = Flask(__name__)

Session = sessionmaker(bind=engine)
session = Session()

@app.route("/")
def index():
    return render_template("login.html")

@app.route("/materiais")
def listar_materiais():
    materiais = session.query(Material).all()
    return render_template("materiais.html", materiais=materiais)

@app.route("/materiais/novo", methods=["GET", "POST"])
def novo_material():
    if request.method == "POST":
        nome = request.form["nome"]
        qtd = request.form["quantidade"]
        novo = Material(nome=nome, quantidade=qtd)
        session.add(novo)
        session.commit()
        return redirect(url_for("listar_materiais"))
    return render_template("novo_material.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
