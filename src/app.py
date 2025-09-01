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

@app.route("/logout")
def logout():
    session.clear()
    flash("Logout realizado com sucesso!", "success")
    return redirect(url_for("index"))


@app.route("/materiais/novo", methods=["GET", "POST"])
def novo_material():
    if "usuario_id" not in session:
        flash("Você precisa estar logado!", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        nome = request.form["nome"]
        quantidade = int(request.form["quantidade"])
        lote = request.form["lote"]
        estoque_minimo_chuva = int(request.form["estoque_minimo_chuva"])
        estoque_minimo_seco = int(request.form["estoque_minimo_seco"])

        novo = Material(
            nome=nome,
            quantidade=quantidade,
            lote=lote,
            estoque_minimo_chuva=estoque_minimo_chuva,
            estoque_minimo_seco=estoque_minimo_seco,
        )

        db_session.add(novo)
        db_session.commit()

        flash("Material cadastrado com sucesso!", "success")
        return redirect(url_for("listar_materiais"))

    return render_template("novo_material.html")


@app.route("/materiais")
def listar_materiais():
    if "usuario_id" not in session:
        flash("Você precisa estar logado!", "error")
        return redirect(url_for("index"))

    materiais = db_session.query(Material).all()
    return render_template("materiais.html", materiais=materiais)

@app.route("/materiais/<int:material_id>/editar", methods=["GET", "POST"])
def editar_material(material_id):
    if "usuario_id" not in session:
        flash("Você precisa estar logado!", "error")
        return redirect(url_for("index"))
    
    material = db_session.query(Material).get(material_id)
    if not material:
        flash("Material não encontrado.", "error")
        return redirect(url_for("listar_materiais"))
    
    if request.method == "POST":
        material.nome = request.form["nome"]
        material.quantidade = int(request.form["quantidade"])
        material.lote = request.form["lote"]
        material.estoque_minimo_chuva = int(request.form["estoque_minimo_chuva"])
        material.estoque_minimo_seco = int(request.form["estoque_minimo_seco"])
        db_session.commit()
        flash("Material atualizado com sucesso!", "success")
        return redirect(url_for("listar_materiais"))
    
    return render_template("editar_material.html", material=material)

@app.route("/materiais/<int:material_id>/excluir", methods=["POST"])
def excluir_material(material_id):
    if "usuario_id" not in session:
        flash("Você precisa estar logado!", "error")
        return redirect(url_for("index"))
    
    material = db_session.query(Material).get(material_id)
    if material:
        db_session.delete(material)
        db_session.commit()
        flash("Material excluído com sucesso!", "success")
    else:
        flash("Material não encontrado.", "error")
    return redirect(url_for("listar_materiais"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
