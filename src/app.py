from flask import Flask, render_template, request, redirect, url_for, session, flash, Blueprint, send_file
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone, date
from models import engine, Usuario, Material, Cliente, Movimentacao
from collections import defaultdict
import io
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from sqlalchemy import or_, and_

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

    user = db.query(Usuario).filter_by(nome=operador, senha=senha).first()

    if user:
        session["usuario_id"] = user.id
        return redirect(url_for("movimentacoes.listar_movimentacoes"))
    else:
        flash("Usuário ou senha inválidos!", "error")
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
        lote = request.form.get("lote", "")  # Agora opcional
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

    nome_filtro = request.args.get("nome", "").strip()

    if nome_filtro:
        materiais = db.query(Material).filter(Material.nome.ilike(f"%{nome_filtro}%")).all()
    else:
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
        material.lote = request.form.get("lote", "")
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

    nome_filtro = request.args.get("nome", "").strip()

    if nome_filtro:
        usuarios = db.query(Usuario).filter(Usuario.nome.ilike(f"%{nome_filtro}%")).all()
    else:
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

    filtro_nome = request.args.get("filtro_nome", "").strip()

    if filtro_nome:
        clientes = db.query(Cliente).filter(Cliente.nome.ilike(f"%{filtro_nome}%")).all()
    else:
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

    cliente_nome = request.args.get("cliente", "").strip()
    material_nome = request.args.get("material", "").strip()
    funcionario_nome = request.args.get("funcionario", "").strip()
    status_raw = request.args.get("status", "").strip().lower()
    data_inicio_str = request.args.get("data_inicio", "").strip()
    data_fim_str = request.args.get("data_fim", "").strip()

    per_page = request.args.get("per_page", 10, type=int)
    page = request.args.get("page", 1, type=int)

    query = db.query(Movimentacao).join(Material).outerjoin(Cliente)

    if cliente_nome:
        query = query.filter(Cliente.nome.ilike(f"%{cliente_nome}%"))

    if material_nome:
        query = query.filter(Material.nome.ilike(f"%{material_nome}%"))

    if funcionario_nome:
        query = query.filter(Movimentacao.funcionario.ilike(f"%{funcionario_nome}%"))

    if status_raw:
        if status_raw in ("verde", "finalizado", "concluido", "concluído"):
            query = query.filter(Movimentacao.status == "verde")

        elif status_raw in ("amarelo", "pendente", "pendentes"):
            query = query.filter(
                or_(
                    Movimentacao.status == "amarelo",
                    and_(Movimentacao.prazo_devolucao != None, Movimentacao.prazo_devolucao < date.today())
                )
            )

        elif status_raw in ("atrasado", "vencido", "overdue"):
            query = query.filter(
                Movimentacao.prazo_devolucao != None,
                Movimentacao.prazo_devolucao < date.today(),
                Movimentacao.devolvido == False,
                Movimentacao.utilizado_cliente == False
            )

        elif status_raw in ("devolvido", "retorno"):
            query = query.filter(Movimentacao.devolvido == True)

        elif status_raw in ("cliente", "ficou no cliente", "utilizado_cliente"):
            query = query.filter(Movimentacao.utilizado_cliente == True)

        elif status_raw in ("amarelo", "vermelho"):
            query = query.filter(Movimentacao.status == status_raw)


    if data_inicio_str:
        try:
            data_inicio = datetime.strptime(data_inicio_str, "%Y-%m-%d")
            query = query.filter(Movimentacao.data_retirada >= data_inicio)
        except ValueError:
            flash("Data de início inválida", "error")

    if data_fim_str:
        try:
            data_fim = datetime.strptime(data_fim_str, "%Y-%m-%d")
            data_fim = data_fim.replace(hour=23, minute=59, second=59)
            query = query.filter(Movimentacao.data_retirada <= data_fim)
        except ValueError:
            flash("Data de fim inválida", "error")

    total = query.count()
    movimentacoes = query.order_by(Movimentacao.data_retirada.desc()) \
                         .offset((page - 1) * per_page) \
                         .limit(per_page) \
                         .all()
    total_pages = (total + per_page - 1) // per_page

    return render_template(
        "movimentacoes.html",
        movimentacoes=movimentacoes,
        page=page,
        total_pages=total_pages,
        per_page=per_page
    )

@movimentacoes_bp.route("/movimentacoes/<int:id>/editar", methods=["GET", "POST"])
def editar_movimentacao(id):
    if "usuario_id" not in session:
        flash("Você precisa estar logado!", "error")
        return redirect(url_for("index"))

    movimentacao = db.query(Movimentacao).get(id)
    if not movimentacao:
        flash("Movimentação não encontrada.", "error")
        return redirect(url_for("movimentacoes.listar_movimentacoes"))

    materiais = db.query(Material).all()
    clientes = db.query(Cliente).all()

    if request.method == "POST":
        try:
            material_id = int(request.form["material_id"])
            quantidade = int(request.form["quantidade"])
            cliente_id = request.form.get("cliente_id")
            cliente_id = int(cliente_id) if cliente_id else None

            ordem_servico = request.form["ordem_servico"].strip()
            funcionario = request.form["funcionario"].strip()

            prazo_str = request.form.get("prazo_devolucao", "").strip()
            prazo_devolucao = datetime.strptime(prazo_str, "%Y-%m-%dT%H:%M") if prazo_str else None

            motivo = request.form.get("motivo", "").strip()
            observacao = request.form.get("observacao", "").strip()

            if movimentacao.material_id != material_id:
                material_antigo = db.query(Material).get(movimentacao.material_id)
                material_antigo.quantidade += movimentacao.quantidade

                material_novo = db.query(Material).get(material_id)
                if material_novo.quantidade < quantidade:
                    flash(f"Estoque insuficiente do material {material_novo.nome}. Estoque atual: {material_novo.quantidade}", "error")
                    return render_template("editar_movimentacao.html", movimentacao=movimentacao, materiais=materiais, clientes=clientes)

                material_novo.quantidade -= quantidade
                movimentacao.material_id = material_id
                movimentacao.quantidade = quantidade
            else:
                diferenca = quantidade - movimentacao.quantidade
                material = db.query(Material).get(material_id)
                if diferenca > 0 and material.quantidade < diferenca:
                    flash(f"Estoque insuficiente! Estoque atual: {material.quantidade}", "error")
                    return render_template("editar_movimentacao.html", movimentacao=movimentacao, materiais=materiais, clientes=clientes)

                material.quantidade -= diferenca
                movimentacao.quantidade = quantidade

            movimentacao.cliente_id = cliente_id
            movimentacao.ordem_servico = ordem_servico
            movimentacao.funcionario = funcionario
            movimentacao.prazo_devolucao = prazo_devolucao
            movimentacao.motivo = motivo or None
            movimentacao.observacao = observacao

            db.commit()
            flash("Movimentação atualizada com sucesso!", "success")
            return redirect(url_for("movimentacoes.listar_movimentacoes"))

        except Exception as e:
            db.rollback()
            flash(f"Erro ao atualizar movimentação: {str(e)}", "error")
            return render_template("editar_movimentacao.html", movimentacao=movimentacao, materiais=materiais, clientes=clientes)

    return render_template("editar_movimentacao.html", movimentacao=movimentacao, materiais=materiais, clientes=clientes)

@movimentacoes_bp.route("/movimentacoes/nova", methods=["GET", "POST"])
def nova_movimentacao():
    if "usuario_id" not in session:
        flash("Você precisa estar logado!", "error")
        return redirect(url_for("index"))

    materiais = db.query(Material).all()
    clientes = db.query(Cliente).all()

    if request.method == "POST":
        try:
            material_id = int(request.form["material_id"])
            quantidade = int(request.form["quantidade"])
            cliente_id = request.form.get("cliente_id")
            cliente_id = int(cliente_id) if cliente_id else None

            ordem_servico = request.form["ordem_servico"].strip()
            funcionario = request.form["funcionario"].strip()

            prazo_str = request.form.get("prazo_devolucao", "").strip()
            prazo_devolucao = datetime.strptime(prazo_str, "%Y-%m-%dT%H:%M") if prazo_str else None

            motivo = request.form.get("motivo", "").strip()
            observacao = request.form.get("observacao", "").strip()

            material = db.query(Material).get(material_id)
            if material.quantidade < quantidade:
                flash(f"Estoque insuficiente! Estoque atual: {material.quantidade}", "error")
                return render_template("nova_movimentacao.html", materiais=materiais, clientes=clientes)

            material.quantidade -= quantidade 

            nova = Movimentacao(
                material_id=material_id,
                quantidade=quantidade,
                cliente_id=cliente_id,
                ordem_servico=ordem_servico,
                funcionario=funcionario,
                responsavel_id=session["usuario_id"],
                data_retirada=datetime.now(timezone.utc),
                prazo_devolucao=prazo_devolucao,
                motivo=motivo or None,
                status="amarelo",
                devolvido=False,
                utilizado_cliente=False,
                funcionando=None,
                observacao=observacao
            )

            db.add(nova)
            db.commit()
            flash("Movimentação registrada com sucesso!", "success")
            return redirect(url_for("movimentacoes.listar_movimentacoes"))

        except Exception as e:
            db.rollback()
            flash(f"Erro ao cadastrar movimentação: {str(e)}", "error")
            return render_template("nova_movimentacao.html", materiais=materiais, clientes=clientes)

    return render_template("nova_movimentacao.html", materiais=materiais, clientes=clientes)

@movimentacoes_bp.route("/movimentacoes/<int:id>/finalizar", methods=["POST"])
def finalizar(id):
    m = db.query(Movimentacao).get(id)
    if not m:
        flash("Movimentação não encontrada", "error")
        return redirect(url_for("movimentacoes.listar_movimentacoes"))

    material = db.query(Material).get(m.material_id)
    funcionando = request.form.get("funcionando")
    destino = request.form.get("destino")

    m.funcionando = True if funcionando == "sim" else False if funcionando == "nao" else None

    if destino == "retorno":
        if not m.devolvido:
            material.quantidade += m.quantidade 
            m.devolvido = True
    elif destino == "cliente":
        m.utilizado_cliente = True
    else:
        flash("Destino inválido", "error")
        return redirect(url_for("movimentacoes.listar_movimentacoes"))

    m.status = "verde"
    db.commit()
    flash("Movimentação finalizada com sucesso!", "success")
    return redirect(url_for("movimentacoes.listar_movimentacoes"))

@movimentacoes_bp.route("/movimentacoes/export/excel")
def export_excel():
    query = db.query(Movimentacao).join(Material).all()

    data = []
    for m in query:
        data.append({
            "Material": m.material.nome,
            "Qtd": m.quantidade,
            "Funcionário": m.funcionario,
            "Cliente": m.cliente.nome if m.cliente else "-",
            "OS": m.ordem_servico,
            "Retirada": m.data_retirada.strftime("%d/%m/%Y %H:%M"),
            "Prazo": m.prazo_devolucao.strftime("%d/%m/%Y") if m.prazo_devolucao else "-",
            "Status": m.status,
            "Observação": m.observacao or "-",
            "Funcionando": "Sim" if m.funcionando else ("Não" if m.funcionando is not None else "-"),
        })

    df = pd.DataFrame(data)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Movimentações")

    output.seek(0)
    return send_file(output, as_attachment=True,
                     download_name="movimentacoes.xlsx",
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@movimentacoes_bp.route("/movimentacoes/export/pdf")
def export_pdf():
    query = db.query(Movimentacao).join(Material).all()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("Relatório de Movimentações", styles["Title"]))

    data = [["Material", "Qtd", "Funcionário", "Cliente", "OS", "Retirada", "Prazo", "Status"]]

    for m in query:
        data.append([
            m.material.nome,
            str(m.quantidade),
            m.funcionario,
            m.cliente.nome if m.cliente else "-",
            m.ordem_servico,
            m.data_retirada.strftime("%d/%m/%Y %H:%M"),
            m.prazo_devolucao.strftime("%d/%m/%Y") if m.prazo_devolucao else "-",
            m.status
        ])

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#ff7b00")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,0), 6),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
    ]))

    elements.append(table)
    doc.build(elements)

    buffer.seek(0)
    return send_file(buffer, as_attachment=True,
                     download_name="movimentacoes.pdf",
                     mimetype="application/pdf")

app.register_blueprint(movimentacoes_bp)


estoque_bp = Blueprint("estoque", __name__, url_prefix="/estoque")

@estoque_bp.route("/")
def controle():
    filtro = request.args.get("filtro", "").strip().lower()
    materiais = db.query(Material).all()

    lotes = defaultdict(list)
    for mat in materiais:
        if not filtro or filtro in mat.nome.lower():
            lotes[mat.lote].append(mat)

    return render_template("controle_estoque.html", lotes=lotes, filtro=filtro)

@estoque_bp.route("/alterar/<int:id>", methods=["POST"])
def alterar(id):
    material = db.query(Material).get(id)
    if not material:
        flash("Material não encontrado!", "error")
        return redirect(url_for("estoque.controle"))

    valor = int(request.form["valor"])
    acao = request.form["acao"]

    if acao == "adicionar":
        material.quantidade += valor
    elif acao == "remover":
        material.quantidade = max(material.quantidade - valor, 0)

    db.commit()
    flash("Estoque atualizado com sucesso!", "success")
    return redirect(url_for("estoque.controle"))

app.register_blueprint(estoque_bp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
