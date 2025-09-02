from flask import Flask, render_template, request, redirect, url_for, session, flash, Blueprint
from sqlalchemy.orm import sessionmaker
from models import engine, Usuario, Material, Cliente, Movimentacao
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.secret_key = "supersecret"

Session = sessionmaker(bind=engine)
db = Session()

@app.route("/")
def index():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():
    operador = request.form["operador"]
    senha = request.form["senha"]

    print(f"Tentando login com -> Operador: {operador}, Senha: {senha}")

    user = db.query(Usuario).filter_by(nome=operador, senha=senha).first()
    print("Resultado query:", user)

    if user:
        session["usuario_id"] = user.id
        print("Login OK, redirecionando...")
        return redirect(url_for("movimentacoes.listar_movimentacoes"))
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

        db.add(novo)
        db.commit()

        flash("Material cadastrado com sucesso!", "success")
        return redirect(url_for("listar_materiais"))

    return render_template("novo_material.html")

@app.route("/materiais")
def listar_materiais():
    if "usuario_id" not in session:
        flash("Você precisa estar logado!", "error")
        return redirect(url_for("index"))

    materiais = db.query(Material).all()
    return render_template("materiais.html", materiais=materiais)

@app.route("/materiais/<int:material_id>/editar", methods=["GET", "POST"])
def editar_material(material_id):
    if "usuario_id" not in session:
        flash("Você precisa estar logado!", "error")
        return redirect(url_for("index"))
    
    material = db.query(Material).get(material_id)
    if not material:
        flash("Material não encontrado.", "error")
        return redirect(url_for("listar_materiais"))
    
    if request.method == "POST":
        material.nome = request.form["nome"]
        material.quantidade = int(request.form["quantidade"])
        material.lote = request.form["lote"]
        material.estoque_minimo_chuva = int(request.form["estoque_minimo_chuva"])
        material.estoque_minimo_seco = int(request.form["estoque_minimo_seco"])
        db.commit()
        flash("Material atualizado com sucesso!", "success")
        return redirect(url_for("listar_materiais"))
    
    return render_template("editar_material.html", material=material)

@app.route("/materiais/<int:material_id>/excluir", methods=["POST"])
def excluir_material(material_id):
    if "usuario_id" not in session:
        flash("Você precisa estar logado!", "error")
        return redirect(url_for("index"))
    
    material = db.query(Material).get(material_id)
    if material:
        db.delete(material)
        db.commit()
        flash("Material excluído com sucesso!", "success")
    else:
        flash("Material não encontrado.", "error")
    return redirect(url_for("listar_materiais"))

@app.route("/usuarios")
def listar_usuarios():
    if "usuario_id" not in session:
        flash("Você precisa estar logado!", "error")
        return redirect(url_for("index"))
    
    usuarios = db.query(Usuario).all()
    return render_template("usuarios.html", usuarios=usuarios)

@app.route("/usuarios/novo", methods=["GET", "POST"])
def novo_usuario():
    if "usuario_id" not in session:
        flash("Você precisa estar logado!", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        nome = request.form["nome"]
        senha = request.form["senha"]

        novo = Usuario(nome=nome, senha=senha)
        db.add(novo)
        db.commit()

        flash("Usuário cadastrado com sucesso!", "success")
        return redirect(url_for("listar_usuarios"))

    return render_template("novo_usuario.html")

@app.route("/usuarios/<int:usuario_id>/editar", methods=["GET", "POST"])
def editar_usuario(usuario_id):
    if "usuario_id" not in session:
        flash("Você precisa estar logado!", "error")
        return redirect(url_for("index"))

    usuario = db.query(Usuario).get(usuario_id)
    if not usuario:
        flash("Usuário não encontrado.", "error")
        return redirect(url_for("listar_usuarios"))

    if request.method == "POST":
        usuario.nome = request.form["nome"]
        nova_senha = request.form.get("senha")
        if nova_senha:
            usuario.senha = nova_senha

        db.commit()
        flash("Usuário atualizado com sucesso!", "success")
        return redirect(url_for("listar_usuarios"))

    return render_template("editar_usuario.html", usuario=usuario)

@app.route('/usuarios/<int:id>/excluir', methods=['POST'])
def excluir_usuario(id):
    usuario = db.get(Usuario, id)
    if not usuario:
        flash("Usuário não encontrado.", "error")
        return redirect(url_for('listar_usuarios'))

    try:
        db.delete(usuario)
        db.commit()
        flash("Usuário excluído com sucesso.", "success")
    except IntegrityError:
        db.rollback()
        flash("Não é possível excluir este usuário, pois ele está vinculado a movimentações.", "error")

    return redirect(url_for('listar_usuarios'))

clientes_bp = Blueprint("clientes", __name__)

@clientes_bp.route("/clientes")
def listar_clientes():
    if "usuario_id" not in session:
        flash("Você precisa estar logado!", "error")
        return redirect(url_for("index"))

    clientes = db.query(Cliente).all()
    return render_template("clientes.html", clientes=clientes)

@clientes_bp.route("/clientes/novo", methods=["GET", "POST"])
def novo_cliente():
    if "usuario_id" not in session:
        flash("Você precisa estar logado!", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        nome = request.form["nome"]
        cliente = Cliente(nome=nome)
        db.add(cliente)
        db.commit()
        flash("Cliente cadastrado com sucesso!", "success")
        return redirect(url_for("clientes.listar_clientes"))

    return render_template("novo_cliente.html")

@clientes_bp.route("/clientes/editar/<int:cliente_id>", methods=["GET", "POST"])
def editar_cliente(cliente_id):
    if "usuario_id" not in session:
        flash("Você precisa estar logado!", "error")
        return redirect(url_for("index"))

    cliente = db.query(Cliente).get(cliente_id)
    if not cliente:
        flash("Cliente não encontrado.", "error")
        return redirect(url_for("clientes.listar_clientes"))

    if request.method == "POST":
        cliente.nome = request.form["nome"]
        db.commit()
        flash("Cliente atualizado com sucesso!", "success")
        return redirect(url_for("clientes.listar_clientes"))

    return render_template("editar_cliente.html", cliente=cliente)

@clientes_bp.route("/clientes/excluir/<int:id>", methods=["POST"])
def excluir_cliente(id):
    if "usuario_id" not in session:
        flash("Você precisa estar logado!", "error")
        return redirect(url_for("index"))

    cliente = db.query(Cliente).get(id)
    if cliente:
        db.delete(cliente)
        db.commit()
        flash("Cliente excluído com sucesso!", "success")
    else:
        flash("Cliente não encontrado.", "error")

    return redirect(url_for("clientes.listar_clientes"))


app.register_blueprint(clientes_bp)

movimentacoes_bp = Blueprint("movimentacoes", __name__)
@movimentacoes_bp.route("/movimentacoes")
def listar_movimentacoes():
    if "usuario_id" not in session:
        flash("Você precisa estar logado!", "error")
        return redirect(url_for("index"))
    
    movimentacoes = db.query(Movimentacao).order_by(Movimentacao.data_retirada.desc()).all()
    return render_template("movimentacoes.html", movimentacoes=movimentacoes)

@movimentacoes_bp.route("/movimentacoes/nova", methods=["GET", "POST"])
def nova_movimentacao():
    if "usuario_id" not in session:
        flash("Você precisa estar logado!", "error")
        return redirect(url_for("index"))
    
    materiais = db.query(Material).all()
    clientes = db.query(Cliente).all()

    if request.method == "POST":
        nova = Movimentacao(
            material_id=request.form["material_id"],
            quantidade=request.form["quantidade"],
            cliente_id=request.form.get("cliente_id") or None,
            ordem_servico=request.form["ordem_servico"],
            funcionario=request.form["funcionario"],
            responsavel_id=session["usuario_id"],
            data_retirada=datetime.utcnow(),
            prazo_devolucao=request.form.get("prazo_devolucao") or None,
            motivo=request.form.get("motivo") or None,
            status=request.form.get("status") or "amarelo",
            devolvido=False,
            utilizado_cliente="utilizado_cliente" in request.form,
            funcionando="funcionando" in request.form,
            observacao=request.form["observacao"]
        )
        db.add(nova)
        db.commit()
        flash("Movimentação registrada com sucesso!", "success")
        return redirect(url_for("movimentacoes.listar_movimentacoes"))

    return render_template("nova_movimentacao.html", materiais=materiais, clientes=clientes)

@movimentacoes_bp.route("/movimentacoes/<int:id>/devolver", methods=["POST"])
def devolver_movimentacao(id):
    movimentacao = db.query(Movimentacao).get(id)
    if not movimentacao:
        flash("Movimentação não encontrada.", "error")
    else:
        movimentacao.devolvido = True
        db.commit()
        flash("Movimentação marcada como devolvida.", "success")
    return redirect(url_for("movimentacoes.listar_movimentacoes"))

app.register_blueprint(movimentacoes_bp)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
