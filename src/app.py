from flask import Flask, render_template, request, redirect, url_for, session, flash, Blueprint, send_file
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone, date
from models import engine, Usuario, Material, Cliente, Movimentacao, MovimentacaoMaterial
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
        lote = request.form.get("lote", "")  
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
    mostrar_somente_nao_ok = request.args.get('mostrar_somente_nao_ok') == '1'

    per_page = request.args.get("per_page", 50, type=int)
    page = request.args.get("page", 1, type=int)

    query = db.query(Movimentacao).join(Movimentacao.materiais).outerjoin(Cliente)

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

    total = query.distinct().count()

    movimentacoes = query.order_by(Movimentacao.data_retirada.desc()) \
                         .offset((page - 1) * per_page) \
                         .limit(per_page) \
                         .all()

    if mostrar_somente_nao_ok:
        movimentacoes = [
            m for m in movimentacoes
            if any(
                mov_mat.quantidade_ok is not None and mov_mat.quantidade_ok < mov_mat.quantidade
                for mov_mat in m.materiais
            )
        ]
        total = len(movimentacoes)
        total_pages = 1
    else:
        total_pages = (total + per_page - 1) // per_page

    materiais_disponiveis = db.query(Material).order_by(Material.nome).all()

    return render_template(
        "movimentacoes.html",
        movimentacoes=movimentacoes,
        page=page,
        total_pages=total_pages,
        per_page=per_page,
        materiais_disponiveis=materiais_disponiveis
    )


@movimentacoes_bp.route("/movimentacoes/nova", methods=["GET", "POST"])
def nova_movimentacao():
    if "usuario_id" not in session:
        flash("Você precisa estar logado!", "error")
        return redirect(url_for("index"))

    materiais = db.query(Material).all()
    clientes = db.query(Cliente).all()

    materiais_serializados = [
        {"id": m.id, "nome": m.nome, "quantidade": m.quantidade}
        for m in materiais
    ]

    if request.method == "POST":
        try:
            ordem_servico = request.form["ordem_servico"].strip()
            funcionario = request.form["funcionario"].strip()
            cliente_id = request.form.get("cliente_id")
            cliente_id = int(cliente_id) if cliente_id else None

            prazo_str = request.form.get("prazo_devolucao", "").strip()
            prazo_devolucao = (
                datetime.strptime(prazo_str, "%Y-%m-%dT%H:%M")
                if prazo_str
                else None
            )

            motivo = request.form.get("motivo", "").strip()
            observacao = request.form.get("observacao", "").strip()

            materiais_ids = request.form.getlist("material_id[]")
            quantidades = request.form.getlist("quantidade[]")

            if not materiais_ids or not quantidades or len(materiais_ids) != len(quantidades):
                flash("Informe pelo menos um material com quantidade!", "error")
                return render_template("nova_movimentacao.html",
                                       materiais=materiais_serializados,
                                       clientes=clientes)

            nova_mov = Movimentacao(
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

            db.add(nova_mov)
            db.flush()

            for mat_id_str, qtd_str in zip(materiais_ids, quantidades):
                mat_id = int(mat_id_str)
                qtd = int(qtd_str)

                material = db.get(Material, mat_id)
                if material.quantidade < qtd:
                    raise Exception(f"Estoque insuficiente de {material.nome}. Estoque atual: {material.quantidade}")

                material.quantidade -= qtd

                mov_mat = MovimentacaoMaterial(
                    movimentacao_id=nova_mov.id,
                    material_id=mat_id,
                    quantidade=qtd
                )
                db.add(mov_mat)

            db.commit()
            flash("Movimentação registrada com sucesso!", "success")
            return redirect(url_for("movimentacoes.listar_movimentacoes"))

        except Exception as e:
            db.rollback()
            import traceback
            traceback.print_exc()
            flash(f"Erro ao cadastrar movimentação: {str(e)}", "error")
            return render_template("nova_movimentacao.html",
                                   materiais=materiais_serializados,
                                   clientes=clientes)

    return render_template("nova_movimentacao.html",
                           materiais=materiais_serializados,
                           clientes=clientes)


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
    materiais_atual = { mm.material_id: mm.quantidade for mm in movimentacao.materiais }

    materiais_serializados = [
        {"id": m.id, "nome": m.nome, "quantidade": m.quantidade}
        for m in materiais
    ]

    if request.method == "POST":
        try:
            ordem_servico = request.form["ordem_servico"].strip()
            funcionario = request.form["funcionario"].strip()
            cliente_id = request.form.get("cliente_id")
            cliente_id = int(cliente_id) if cliente_id else None

            prazo_str = request.form.get("prazo_devolucao", "").strip()
            prazo_devolucao = (
                datetime.strptime(prazo_str, "%Y-%m-%dT%H:%M")
                if prazo_str
                else None
            )

            motivo = request.form.get("motivo", "").strip()
            observacao = request.form.get("observacao", "").strip()

            materiais_ids = request.form.getlist("material_id[]")
            quantidades = request.form.getlist("quantidade[]")

            if not materiais_ids or not quantidades or len(materiais_ids) != len(quantidades):
                flash("Informe pelo menos um material com quantidade!", "error")
                return render_template("editar_movimentacao.html",
                                       movimentacao=movimentacao,
                                       materiais=materiais_serializados,
                                       clientes=clientes)

            novos_materiais = {}
            for mat_id_str, qtd_str in zip(materiais_ids, quantidades):
                mat_id = int(mat_id_str)
                qtd = int(qtd_str)
                novos_materiais[mat_id] = qtd

            for mat_id, qtd_atual in materiais_atual.items():
                qtd_nova = novos_materiais.get(mat_id, 0)
                diferenca = qtd_atual - qtd_nova
                if diferenca > 0:
                    material = db.query(Material).get(mat_id)
                    material.quantidade += diferenca

            for mat_id, qtd_nova in novos_materiais.items():
                qtd_atual = materiais_atual.get(mat_id, 0)
                diferenca = qtd_nova - qtd_atual
                if diferenca > 0:
                    material = db.query(Material).get(mat_id)
                    if material.quantidade < diferenca:
                        flash(f"Estoque insuficiente do material {material.nome}. Estoque atual: {material.quantidade}", "error")
                        return render_template("editar_movimentacao.html",
                                               movimentacao=movimentacao,
                                               materiais=materiais_serializados,
                                               clientes=clientes)
                    material.quantidade -= diferenca

            db.query(MovimentacaoMaterial).filter(MovimentacaoMaterial.movimentacao_id == movimentacao.id).delete()

            for mat_id, qtd in novos_materiais.items():
                mov_mat = MovimentacaoMaterial(
                    movimentacao_id=movimentacao.id,
                    material_id=mat_id,
                    quantidade=qtd
                )
                db.add(mov_mat)

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
            import traceback
            traceback.print_exc()
            flash(f"Erro ao atualizar movimentação: {str(e)}", "error")
            return render_template("editar_movimentacao.html",
                                   movimentacao=movimentacao,
                                   materiais=materiais_serializados,
                                   clientes=clientes)

    return render_template("editar_movimentacao.html",
                           movimentacao=movimentacao,
                           materiais=materiais_serializados,
                           clientes=clientes)
@movimentacoes_bp.route("/movimentacoes/<int:id>/finalizar", methods=["POST"])
def finalizar(id):
    if "usuario_id" not in session:
        flash("Você precisa estar logado!", "error")
        return redirect(url_for("index"))

    m = db.query(Movimentacao).get(id)
    if not m:
        flash("Movimentação não encontrada", "error")
        return redirect(url_for("movimentacoes.listar_movimentacoes"))

    try:
        for mm in m.materiais:
            input_name = f"quantidade_ok_{mm.id}"
            qtd_ok_str = request.form.get(input_name)

            try:
                qtd_ok = int(qtd_ok_str)
                if qtd_ok < 0 or qtd_ok > mm.quantidade:
                    flash(f"Quantidade inválida para o material {mm.material.nome}", "error")
                    return redirect(url_for("movimentacoes.listar_movimentacoes"))

                mm.quantidade_ok = qtd_ok

                material = db.query(Material).get(mm.material_id)
                material.quantidade += qtd_ok

            except (ValueError, TypeError):
                flash(f"Quantidade inválida para o material {mm.material.nome}", "error")
                return redirect(url_for("movimentacoes.listar_movimentacoes"))

        # Apenas a observação do usuário
        m.observacao = request.form.get("observacao_finalizacao", "").strip()
        m.devolvido = True
        m.status = "verde"

        db.commit()
        flash("Movimentação finalizada com sucesso!", "success")
        return redirect(url_for("movimentacoes.listar_movimentacoes"))

    except Exception as e:
        db.rollback()
        flash(f"Erro ao finalizar movimentação: {str(e)}", "error")
        return redirect(url_for("movimentacoes.listar_movimentacoes"))


@movimentacoes_bp.route("/movimentacoes/export/excel")
def export_excel():
    query = db.query(Movimentacao).outerjoin(Movimentacao.materiais).outerjoin(Material).outerjoin(Cliente)

    material = request.args.get("material")
    cliente = request.args.get("cliente")
    funcionario = request.args.get("funcionario")
    status = request.args.get("status")
    data_inicio = request.args.get("data_inicio")
    data_fim = request.args.get("data_fim")

    if material:
        query = query.filter(Material.nome.ilike(f"%{material}%"))
    if cliente:
        query = query.filter(Cliente.nome.ilike(f"%{cliente}%"))
    if funcionario:
        query = query.filter(Movimentacao.funcionario.ilike(f"%{funcionario}%"))
    if status:
        query = query.filter(Movimentacao.status == status)
    if data_inicio:
        query = query.filter(Movimentacao.data_retirada >= data_inicio)
    if data_fim:
        query = query.filter(Movimentacao.data_retirada <= data_fim)

    movimentacoes = query.distinct().all()

    data = []
    for mov in movimentacoes:
        for mm in mov.materiais:
            material = mm.material
            data.append({
                "Material": material.nome,
                "Qtd": mm.quantidade,
                "Funcionário": mov.funcionario,
                "Cliente": mov.cliente.nome if mov.cliente else "-",
                "OS": mov.ordem_servico,
                "Retirada": mov.data_retirada.strftime("%d/%m/%Y %H:%M"),
                "Prazo": mov.prazo_devolucao.strftime("%d/%m/%Y") if mov.prazo_devolucao else "-",
                "Status": mov.status,
                "Observação": mov.observacao or "-",
                "Funcionando": "Sim" if mov.funcionando else ("Não" if mov.funcionando is not None else "-"),
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
    query = db.query(Movimentacao).outerjoin(Movimentacao.materiais).outerjoin(Material).outerjoin(Cliente)

    material = request.args.get("material")
    cliente = request.args.get("cliente")
    funcionario = request.args.get("funcionario")
    status = request.args.get("status")
    data_inicio = request.args.get("data_inicio")
    data_fim = request.args.get("data_fim")

    if material:
        query = query.filter(Material.nome.ilike(f"%{material}%"))
    if cliente:
        query = query.filter(Cliente.nome.ilike(f"%{cliente}%"))
    if funcionario:
        query = query.filter(Movimentacao.funcionario.ilike(f"%{funcionario}%"))
    if status:
        query = query.filter(Movimentacao.status == status)
    if data_inicio:
        query = query.filter(Movimentacao.data_retirada >= data_inicio)
    if data_fim:
        query = query.filter(Movimentacao.data_retirada <= data_fim)

    movimentacoes = query.distinct().all()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("Relatório de Movimentações", styles["Title"]))

    data = [["Material", "Qtd", "Funcionário", "Cliente", "OS", "Retirada", "Prazo", "Status"]]

    for mov in movimentacoes:
        for mm in mov.materiais:
            material = mm.material
            data.append([
                material.nome,
                str(mm.quantidade),
                mov.funcionario,
                mov.cliente.nome if mov.cliente else "-",
                mov.ordem_servico,
                mov.data_retirada.strftime("%d/%m/%Y %H:%M"),
                mov.prazo_devolucao.strftime("%d/%m/%Y") if mov.prazo_devolucao else "-",
                mov.status
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
