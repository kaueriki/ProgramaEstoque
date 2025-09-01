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

# LISTAR USUÁRIOS
@app.route("/usuarios")
def listar_usuarios():
    if "usuario_id" not in session:
        flash("Você precisa estar logado!", "error")
        return redirect(url_for("index"))
    
    usuarios = db_session.query(Usuario).all()
    return render_template("usuarios.html", usuarios=usuarios)


# NOVO USUÁRIO
@app.route("/usuarios/novo", methods=["GET", "POST"])
def novo_usuario():
    if "usuario_id" not in session:
        flash("Você precisa estar logado!", "error")
        return redirect(url_for("index"))
    
    if request.method == "POST":
        nome = request.form["nome"]
        email = request.form["email"]
        perfil = request.form["perfil"]
        senha = request.form["senha"]

        # Aqui você pode adicionar validação, criptografia da senha, etc.

        novo = Usuario(nome=nome, email=email, perfil=perfil, senha=senha)

        db_session.add(novo)
        db_session.commit()
        
        flash("Usuário cadastrado com sucesso!", "success")
        return redirect(url_for("listar_usuarios"))
    
    return render_template("novo_usuario.html")


# EDITAR USUÁRIO
@app.route("/usuarios/<int:usuario_id>/editar", methods=["GET", "POST"])
def editar_usuario(usuario_id):
    if "usuario_id" not in session:
        flash("Você precisa estar logado!", "error")
        return redirect(url_for("index"))
    
    usuario = db_session.query(Usuario).get(usuario_id)
    if not usuario:
        flash("Usuário não encontrado.", "error")
        return redirect(url_for("listar_usuarios"))
    
    if request.method == "POST":
        usuario.nome = request.form["nome"]
        usuario.email = request.form["email"]
        usuario.perfil = request.form["perfil"]
        # Se quiser permitir mudar senha, faça aqui. Caso contrário, remova.
        nova_senha = request.form.get("senha")
        if nova_senha:
            usuario.senha = nova_senha
        
        db_session.commit()
        flash("Usuário atualizado com sucesso!", "success")
        return redirect(url_for("listar_usuarios"))
    
    return render_template("editar_usuario.html", usuario=usuario)


# EXCLUIR USUÁRIO
@app.route("/usuarios/<int:usuario_id>/excluir", methods=["POST"])
def excluir_usuario(usuario_id):
    if "usuario_id" not in session:
        flash("Você precisa estar logado!", "error")
        return redirect(url_for("index"))
    
    usuario = db_session.query(Usuario).get(usuario_id)
    if usuario:
        db_session.delete(usuario)
        db_session.commit()
        flash("Usuário excluído com sucesso!", "success")
    else:
        flash("Usuário não encontrado.", "error")
    
    return redirect(url_for("listar_usuarios"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
