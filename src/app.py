from flask import Flask, render_template, request, redirect, url_for, session, flash, Blueprint, send_file
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone, date
from models import engine, Usuario, Material, Cliente, Movimentacao, MovimentacaoMaterial, Colaborador
from collections import defaultdict
import io
import pandas as pd
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from sqlalchemy import or_, and_
import os
from decimal import Decimal

app = Flask(__name__)
app.secret_key = "supersecret"

Session = sessionmaker(bind=engine)
db = Session()

@app.errorhandler(500)
def internal_error(error):
    db.rollback() 
    return render_template("500.html"), 500

@app.errorhandler(404)
def not_found_error(error):
    return render_template("404.html"), 404

@app.route("/")
def index():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():
    operador = request.form["operador"]
    senha = request.form["senha"]

    try:
        user = db.query(Usuario).filter_by(nome=operador, senha=senha).first()

        if user:
            session["usuario_id"] = user.id
            return redirect(url_for("movimentacoes.listar_movimentacoes"))
        else:
            flash("Usuário ou senha inválidos!", "error")
            return redirect(url_for("index"))

    except Exception as e:
        db.rollback() 
        print(f"[ERRO LOGIN] {e}")
        flash("Erro interno ao tentar logar. Tente novamente mais tarde.", "error")
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
        unidade_medida = request.form["unidade_medida"]
        lote = request.form.get("lote", "")  
        estoque_minimo_chuva = int(request.form["estoque_minimo_chuva"])
        estoque_minimo_seco = int(request.form["estoque_minimo_seco"])

        novo = Material(
            nome=nome,
            quantidade=quantidade,
            unidade_medida=unidade_medida,
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
        material.quantidade = Decimal(request.form["quantidade"])
        material.unidade_medida = request.form["unidade_medida"]
        material.lote = request.form.get("lote", "")
        material.estoque_minimo_chuva = Decimal(request.form["estoque_minimo_chuva"])
        material.estoque_minimo_seco = Decimal(request.form["estoque_minimo_seco"])
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
    os_numero = request.args.get("os", "").strip()

    mostrar_somente_nao_ok = request.args.get("mostrar_somente_nao_ok") == "1"
    mostrar_somente_ok = request.args.get("mostrar_somente_ok") == "1"
    mostrar_ficou_cliente = request.args.get("mostrar_ficou_cliente") == "1"

    per_page = request.args.get("per_page", 100, type=int)
    page = request.args.get("page", 1, type=int)

    query = db.query(Movimentacao).options(
        joinedload(Movimentacao.materiais).joinedload(MovimentacaoMaterial.material),
        joinedload(Movimentacao.cliente)
    )

    if cliente_nome:
        query = query.join(Movimentacao.cliente).filter(
            Cliente.nome.ilike(f"%{cliente_nome}%")
        )

    if material_nome:
        query = query.join(Movimentacao.materiais).join(
            MovimentacaoMaterial.material
        ).filter(
            Material.nome.ilike(f"%{material_nome}%")
        )

    if funcionario_nome:
        query = query.filter(
            Movimentacao.funcionario.ilike(f"%{funcionario_nome}%")
        )

    if os_numero:
        query = query.filter(
            Movimentacao.ordem_servico.ilike(f"%{os_numero}%")
        )

    # Filtro por datas (data de retirada)
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

    query = query.order_by(Movimentacao.data_retirada.desc())

    movimentacoes_all = query.all()

    # ---- Cálculo de status em memória ----
    def materiais_finalizados(mov):
        # material é considerado finalizado se tem quantidade_ok ou quantidade_sem_retorno preenchido
        return all(
            (mov_mat.quantidade_ok is not None or mov_mat.quantidade_sem_retorno is not None)
            for mov_mat in mov.materiais
        )

    def status_calculado(mov):
        # 1) se todos os materiais estão tratados -> FINALIZADO
        if materiais_finalizados(mov):
            return "finalizado"
        # 2) se ainda tem pendência e prazo já venceu -> ATRASADO
        if mov.prazo_devolucao and mov.prazo_devolucao < date.today():
            return "atrasado"
        # 3) caso contrário -> PENDENTE
        return "pendente"

    # aplica status em memória
    movimentacoes_status = [(m, status_calculado(m)) for m in movimentacoes_all]

    if status_raw:
        movimentacoes_all = [
            m for (m, st) in movimentacoes_status if st == status_raw
        ]
    else:
        movimentacoes_all = [m for (m, st) in movimentacoes_status]

    # ---- filtros extras: RETORNO OK / NÃO OK / SEM RETORNO ----
    if mostrar_somente_nao_ok:
        movimentacoes_filtradas = [
            m for m in movimentacoes_all
            if any(
                # retorno NÃO OK = diferença entre retirado e (OK + sem retorno) > 0
                (mov_mat.quantidade_ok is not None and mov_mat.quantidade_ok < mov_mat.quantidade)
                or (mov_mat.quantidade_sem_retorno is not None and mov_mat.quantidade_sem_retorno > 0)
                for mov_mat in m.materiais
            )
        ]
    elif mostrar_somente_ok:
        movimentacoes_filtradas = [
            m for m in movimentacoes_all
            if all(
                mov_mat.quantidade_ok == mov_mat.quantidade
                and (mov_mat.quantidade_sem_retorno or 0) == 0
                for mov_mat in m.materiais
            )
        ]
    elif mostrar_ficou_cliente:
        movimentacoes_filtradas = [
            m for m in movimentacoes_all
            if any(
                (mov_mat.quantidade_sem_retorno or 0) > 0
                for mov_mat in m.materiais
            )
        ]
    else:
        movimentacoes_filtradas = movimentacoes_all

    # ---- paginação ----
    total = len(movimentacoes_filtradas)
    total_pages = (total + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    movimentacoes_paginated = movimentacoes_filtradas[start:end]

    # materiais disponíveis para selects, etc.
    materiais_disponiveis = db.query(Material).order_by(Material.nome).all()
    materiais_serializados = [
        {
            "id": m.id,
            "nome": m.nome,
            "quantidade": Decimal(m.quantidade or 0),
            "unidade_medida": m.unidade_medida,
            "lote": m.lote,
            "estoque_minimo_chuva": Decimal(m.estoque_minimo_chuva or 0),
            "estoque_minimo_seco": Decimal(m.estoque_minimo_seco or 0),
        }
        for m in materiais_disponiveis
    ]

    return render_template(
        "movimentacoes.html",
        movimentacoes=movimentacoes_paginated,
        page=page,
        total_pages=total_pages,
        per_page=per_page,
        materiais_disponiveis=materiais_serializados,
        materiais=materiais_serializados,
    )

@movimentacoes_bp.route("/movimentacoes/nova", methods=["GET", "POST"])
def nova_movimentacao():
    if "usuario_id" not in session:
        flash("Você precisa estar logado!", "error")
        return redirect(url_for("index"))

    materiais = db.query(Material).all()
    clientes = db.query(Cliente).all()
    colaboradores = [c.nome for c in db.query(Colaborador).all()]

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

            data_retirada_str = request.form.get("data_retirada", "").strip()
            data_retirada = (
                datetime.strptime(data_retirada_str, "%Y-%m-%dT%H:%M")
                if data_retirada_str
                else None
            )

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
                                       clientes=clientes,
                                       colaboradores=colaboradores)

            nova_mov = Movimentacao(
                cliente_id=cliente_id,
                ordem_servico=ordem_servico,
                funcionario=funcionario,
                responsavel_id=session["usuario_id"],
                data_retirada=data_retirada,
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
                if not mat_id_str.isdigit():
                    continue

                mat_id = int(mat_id_str)
                qtd = Decimal(qtd_str)

                material = db.get(Material, mat_id)
                if material.quantidade < qtd:
                    raise Exception(f"Estoque insuficiente de {material.nome}. Estoque atual: {material.quantidade}")

                material.quantidade -= qtd

                mov_mat = MovimentacaoMaterial(
                    movimentacao_id=nova_mov.id,
                    material_id=mat_id,
                    quantidade=qtd,
                    quantidade_ok=None,
                    quantidade_sem_retorno=None
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
                                   clientes=clientes,
                                   colaboradores=colaboradores)


    return render_template("nova_movimentacao.html",
                           materiais=materiais_serializados,
                           clientes=clientes,
                           colaboradores=colaboradores)

import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

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
    colaboradores = [c.nome for c in db.query(Colaborador).all()]

    materiais_json = [
        {"id": m.id, "nome": m.nome, "quantidade": m.quantidade}
        for m in materiais
    ]

    if request.method == "POST":
        try:
            ordem_servico = request.form["ordem_servico"].strip()
            funcionario = request.form["funcionario"].strip()
            cliente_id = request.form.get("cliente_id")
            cliente_id = int(cliente_id) if cliente_id else None

            data_retirada_str = request.form.get("data_retirada", "").strip()
            data_retirada = (
                datetime.strptime(data_retirada_str, "%Y-%m-%dT%H:%M")
                if data_retirada_str else None
            )

            prazo_str = request.form.get("prazo_devolucao", "").strip()
            prazo_devolucao = (
                datetime.strptime(prazo_str, "%Y-%m-%dT%H:%M")
                if prazo_str else None
            )

            motivo = request.form.get("motivo", "").strip()
            observacao = request.form.get("observacao", "").strip()

            materiais_ids = request.form.getlist("material_id[]")
            quantidades = request.form.getlist("quantidade[]")
            quantidades_ok = request.form.getlist("quantidade_ok[]")
            quantidades_sem_retorno = request.form.getlist("quantidade_sem_retorno[]")

            if not materiais_ids or not quantidades or len(materiais_ids) != len(quantidades):
                flash("Informe pelo menos um material com quantidade!", "error")
                return render_template(
                    "editar_movimentacao.html",
                    movimentacao=movimentacao,
                    materiais=materiais,
                    clientes=clientes,
                    colaboradores=colaboradores,
                    materiais_json=materiais_json
                )

            for mm in movimentacao.materiais:
                material = db.query(Material).get(mm.material_id)
                if not material:
                    continue
                    
                quantidade_a_repor = mm.quantidade - (mm.quantidade_ok or 0)
                material.quantidade += quantidade_a_repor


            db.query(MovimentacaoMaterial).filter_by(
                movimentacao_id=movimentacao.id
            ).delete()
            db.flush()

            for i, (mat_id_str, qtd_str) in enumerate(zip(materiais_ids, quantidades)):
                mat_id = int(mat_id_str)
                qtd = Decimal(qtd_str or 0)
                qtd_ok = Decimal(quantidades_ok[i]) if i < len(quantidades_ok) and quantidades_ok[i].strip() else Decimal(0)
                qtd_sem_retorno = Decimal(quantidades_sem_retorno[i]) if i < len(quantidades_sem_retorno) and quantidades_sem_retorno[i].strip() else Decimal(0)

                material = db.query(Material).get(mat_id)
                if not material:
                    raise Exception(f"Material ID {mat_id} não encontrado.")

                if qtd_ok + qtd_sem_retorno > qtd:
                    raise Exception(f"A soma de OK e Sem Retorno do material {material.nome} ultrapassa a quantidade retirada.")

                if material.quantidade < qtd:
                    raise Exception(f"Estoque insuficiente para {material.nome}. Disponível: {material.quantidade}")
                material.quantidade -= qtd

                if qtd_ok > 0:
                    material.quantidade += qtd_ok

                mov_mat = MovimentacaoMaterial(
                    movimentacao_id=movimentacao.id,
                    material_id=mat_id,
                    quantidade=qtd,
                    quantidade_ok=qtd_ok if qtd_ok > 0 else None,
                    quantidade_sem_retorno=qtd_sem_retorno if qtd_sem_retorno > 0 else None
                )
                db.add(mov_mat)

                print(f"[DEBUG] {material.nome}: qtd={qtd}, ok={qtd_ok}, sem_retorno={qtd_sem_retorno}, estoque_final={material.quantidade}")

            movimentacao.cliente_id = cliente_id
            movimentacao.ordem_servico = ordem_servico
            movimentacao.funcionario = funcionario
            movimentacao.data_retirada = data_retirada
            movimentacao.prazo_devolucao = prazo_devolucao
            movimentacao.motivo = motivo or None
            movimentacao.observacao = observacao

            db.flush()
            movimentacao.materiais = db.query(MovimentacaoMaterial).filter_by(
                movimentacao_id=movimentacao.id
            ).all()

            total_materiais = len(movimentacao.materiais)
            total_processados = sum(
                1 for mm in movimentacao.materiais
                if mm.quantidade_ok is not None or mm.quantidade_sem_retorno is not None
            )

            if total_processados == total_materiais and total_materiais > 0:
                if any((mm.quantidade_sem_retorno or 0) > 0 for mm in movimentacao.materiais):
                    movimentacao.status = "amarelo"
                    movimentacao.devolvido = False
                    movimentacao.utilizado_cliente = True
                else:
                    movimentacao.status = "verde"
                    movimentacao.devolvido = True
                    movimentacao.utilizado_cliente = False
            else:
                movimentacao.status = "amarelo"
                movimentacao.devolvido = False
                movimentacao.utilizado_cliente = any((mm.quantidade_sem_retorno or 0) > 0 for mm in movimentacao.materiais)

            db.commit()
            flash("Movimentação atualizada com sucesso! Estoque sincronizado.", "success")
            return redirect(url_for("movimentacoes.listar_movimentacoes"))

        except Exception as e:
            db.rollback()
            import traceback
            traceback.print_exc()
            flash(f"Erro ao atualizar movimentação: {str(e)}", "error")
            return render_template(
                "editar_movimentacao.html",
                movimentacao=movimentacao,
                materiais=materiais,
                clientes=clientes,
                colaboradores=colaboradores,
                materiais_json=materiais_json
            )

    return render_template(
        "editar_movimentacao.html",
        movimentacao=movimentacao,
        materiais=materiais,
        clientes=clientes,
        colaboradores=colaboradores,
        materiais_json=materiais_json
    )

@movimentacoes_bp.route("/movimentacoes/<int:id>/finalizar", methods=["POST"])
def finalizar_movimentacao(id):
    if "usuario_id" not in session:
        flash("Você precisa estar logado!", "error")
        return redirect(url_for("index"))

    movimentacao = db.query(Movimentacao).get(id)
    if not movimentacao:
        flash("Movimentação não encontrada.", "error")
        return redirect(url_for("movimentacoes.listar_movimentacoes"))

    try:
        funcionando_str = request.form.get("funcionando")
        funcionando = None
        if funcionando_str is not None:
            funcionando = funcionando_str.lower() in ("sim", "true", "1")
        movimentacao.funcionando = funcionando

        total_materiais = len(movimentacao.materiais)
        total_processados = 0

        for mm in movimentacao.materiais:
            input_ok = f"quantidade_ok_{mm.id}"
            input_sem_retorno = f"quantidade_sem_retorno_{mm.id}"

            qtd_ok_str = request.form.get(input_ok)
            qtd_sem_retorno_str = request.form.get(input_sem_retorno)

            if (qtd_ok_str is None or qtd_ok_str.strip() == "") and \
               (qtd_sem_retorno_str is None or qtd_sem_retorno_str.strip() == ""):
                mm.quantidade_ok = None
                mm.quantidade_sem_retorno = None
                continue

            qtd_ok = Decimal(qtd_ok_str) if qtd_ok_str and qtd_ok_str.strip() != "" else 0
            qtd_sem_retorno = Decimal(qtd_sem_retorno_str) if qtd_sem_retorno_str and qtd_sem_retorno_str.strip() != "" else 0

            if qtd_ok < 0 or qtd_sem_retorno < 0:
                flash(f"Quantidades não podem ser negativas para o material {mm.material.nome}.", "error")
                return redirect(url_for("movimentacoes.listar_movimentacoes"))

            total_informado = qtd_ok + qtd_sem_retorno
            if total_informado > mm.quantidade:
                flash(f"A soma das quantidades do material {mm.material.nome} não pode ultrapassar a retirada ({mm.quantidade}).", "error")
                return redirect(url_for("movimentacoes.listar_movimentacoes"))

            mm.retorno_nao_ok = mm.quantidade - total_informado if total_informado < mm.quantidade else 0
            mm.quantidade_ok = qtd_ok
            mm.quantidade_sem_retorno = qtd_sem_retorno

            if qtd_ok > 0:
                material = db.query(Material).get(mm.material_id)
                material.quantidade += qtd_ok

            total_processados += 1

        observacao = request.form.get("observacao_finalizacao", "").strip()
        if observacao:
            movimentacao.observacao = observacao

        pendente = any(
            mm.quantidade_ok is None and mm.quantidade_sem_retorno is None for mm in movimentacao.materiais
        )
        processados_todos = total_processados == total_materiais

        if total_processados == 0 or pendente:
            movimentacao.status = "amarelo"
            movimentacao.devolvido = False
            movimentacao.utilizado_cliente = False
        elif processados_todos:
            movimentacao.status = "verde"
            movimentacao.devolvido = all(
                mm.quantidade_ok == mm.quantidade and mm.retorno_nao_ok == 0 and mm.quantidade_sem_retorno == 0
                for mm in movimentacao.materiais
            )
            movimentacao.utilizado_cliente = all(
                mm.quantidade_sem_retorno == mm.quantidade and mm.quantidade_ok == 0 and mm.retorno_nao_ok == 0
                for mm in movimentacao.materiais
            )
        else:
            movimentacao.status = "amarelo"
            movimentacao.devolvido = False
            movimentacao.utilizado_cliente = False

        db.commit()
        flash("Finalização processada com sucesso!", "success")
        return redirect(url_for("movimentacoes.listar_movimentacoes"))

    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        flash(f"Erro ao finalizar movimentação: {str(e)}", "error")
        return redirect(url_for("movimentacoes.listar_movimentacoes"))

@movimentacoes_bp.route("/movimentacoes/<int:id>/excluir", methods=["POST"])
def excluir_movimentacao(id):
    if "usuario_id" not in session:
        flash("Você precisa estar logado!", "error")
        return redirect(url_for("index"))

    movimentacao = db.query(Movimentacao).get(id)
    if not movimentacao:
        flash("Movimentação não encontrada.", "error")
        return redirect(url_for("movimentacoes.listar_movimentacoes"))

    try:
        for mm in movimentacao.materiais:
            material = db.query(Material).get(mm.material_id)
            if material:
                qtd_retirada = mm.quantidade or 0
                qtd_devolvida = mm.quantidade_ok or 0
                material.quantidade += qtd_retirada - qtd_devolvida

        db.delete(movimentacao)
        db.commit()
        flash("Movimentação excluída com sucesso!", "success")

    except Exception as e:
        db.rollback()
        flash(f"Erro ao excluir movimentação: {str(e)}", "error")

    return redirect(url_for("movimentacoes.listar_movimentacoes"))

@movimentacoes_bp.route("/movimentacoes/export/excel")
def export_excel():
    query = db.query(Movimentacao).outerjoin(Movimentacao.materiais).outerjoin(Material).outerjoin(Cliente)

    material_filtro = request.args.get("material", "").strip()
    cliente_filtro = request.args.get("cliente", "").strip()
    funcionario_filtro = request.args.get("funcionario", "").strip()
    status_filtro = request.args.get("status", "").strip().lower()
    data_inicio = request.args.get("data_inicio", "").strip()
    data_fim = request.args.get("data_fim", "").strip()

    if material_filtro:
        query = query.filter(Material.nome.ilike(f"%{material_filtro}%"))
    if cliente_filtro:
        query = query.filter(Cliente.nome.ilike(f"%{cliente_filtro}%"))
    if funcionario_filtro:
        query = query.filter(Movimentacao.funcionario.ilike(f"%{funcionario_filtro}%"))

    if status_filtro:
        if status_filtro == "devolvido":
            query = query.filter(Movimentacao.devolvido.is_(True))
        elif status_filtro == "cliente":
            query = query.filter(Movimentacao.utilizado_cliente.is_(True))
        elif status_filtro == "atrasado":
            query = query.filter(
                and_(
                    Movimentacao.devolvido.is_(False),
                    Movimentacao.utilizado_cliente.is_(False),
                    Movimentacao.prazo_devolucao != None,
                    Movimentacao.prazo_devolucao < date.today()
                )
            )
        elif status_filtro == "pendente":
            query = query.filter(
                and_(
                    Movimentacao.devolvido.is_(False),
                    Movimentacao.utilizado_cliente.is_(False),
                    or_(
                        Movimentacao.prazo_devolucao == None,
                        Movimentacao.prazo_devolucao >= date.today()
                    )
                )
            )
        elif status_filtro in ("verde", "amarelo", "vermelho"):
            query = query.filter(Movimentacao.status == status_filtro)

    if data_inicio:
        try:
            dt_inicio = datetime.strptime(data_inicio, "%Y-%m-%d")
            query = query.filter(Movimentacao.data_retirada >= dt_inicio)
        except ValueError:
            flash("Formato de data início inválido.", "error")

    if data_fim:
        try:
            dt_fim = datetime.strptime(data_fim, "%Y-%m-%d")
            query = query.filter(Movimentacao.data_retirada <= dt_fim)
        except ValueError:
            flash("Formato de data fim inválido.", "error")

    movimentacoes = query.distinct().all()

    data = []

    for mov in movimentacoes:
        status_atual = mov.status_atual 

        if mov.materiais:
            for mm in mov.materiais:
                material = mm.material
                data.append({
                    "Material": material.nome if material else "-",
                    "Qtd": mm.quantidade,
                    "Qtd OK": mm.quantidade_ok if (mov.devolvido or mov.utilizado_cliente) else "-",
                    "Qtd NÃO OK": (
                        (mm.quantidade - (mm.quantidade_ok or 0) - (mm.quantidade_sem_retorno or 0))
                        if (mov.devolvido or mov.utilizado_cliente) else "-"
                    ),
                    "Ficou Cliente": mm.quantidade_sem_retorno if (mov.devolvido or mov.utilizado_cliente) else "-",
                    "Funcionário": mov.funcionario,
                    "Cliente": mov.cliente.nome if mov.cliente else "-",
                    "OS": mov.ordem_servico or "-",
                    "Retirada": mov.data_retirada.strftime("%d/%m/%Y %H:%M") if mov.data_retirada else "-",
                    "Prazo": mov.prazo_devolucao.strftime("%d/%m/%Y") if mov.prazo_devolucao else "-",
                    "Status": status_atual,
                    "Observação": mov.observacao or "-",
                    "Funcionando": "Sim" if mov.funcionando else ("Não" if mov.funcionando is not None else "-"),
                })
        else:
            data.append({
                "Material": "-",
                "Qtd": "-",
                "Qtd OK": "-",
                "Qtd NÃO OK": "-",
                "Ficou Cliente": "-",
                "Funcionário": mov.funcionario,
                "Cliente": mov.cliente.nome if mov.cliente else "-",
                "OS": mov.ordem_servico or "-",
                "Retirada": mov.data_retirada.strftime("%d/%m/%Y %H:%M") if mov.data_retirada else "-",
                "Prazo": mov.prazo_devolucao.strftime("%d/%m/%Y") if mov.prazo_devolucao else "-",
                "Status": status_atual,
                "Observação": mov.observacao or "-",
                "Funcionando": "Sim" if mov.funcionando else ("Não" if mov.funcionando is not None else "-"),
            })

    df = pd.DataFrame(data)
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Movimentações")

    output.seek(0)

    if not data:
        flash("Não há movimentações para exportar com os filtros aplicados.", "info")

    return send_file(
        output,
        as_attachment=True,
        download_name="movimentacoes.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@movimentacoes_bp.route("/movimentacoes/export/pdf")
def export_pdf():
    query = db.query(Movimentacao).outerjoin(Movimentacao.materiais).outerjoin(Material).outerjoin(Cliente)

    material_filtro = request.args.get("material", "").strip()
    cliente_filtro = request.args.get("cliente", "").strip()
    funcionario_filtro = request.args.get("funcionario", "").strip()
    status_filtro = request.args.get("status", "").strip().lower()
    data_inicio = request.args.get("data_inicio", "").strip()
    data_fim = request.args.get("data_fim", "").strip()

    if material_filtro:
        query = query.filter(Material.nome.ilike(f"%{material_filtro}%"))
    if cliente_filtro:
        query = query.filter(Cliente.nome.ilike(f"%{cliente_filtro}%"))
    if funcionario_filtro:
        query = query.filter(Movimentacao.funcionario.ilike(f"%{funcionario_filtro}%"))

    if status_filtro:
        if status_filtro == "devolvido":
            query = query.filter(Movimentacao.devolvido.is_(True))
        elif status_filtro == "cliente":
            query = query.filter(Movimentacao.utilizado_cliente.is_(True))
        elif status_filtro == "atrasado":
            query = query.filter(
                and_(
                    Movimentacao.devolvido.is_(False),
                    Movimentacao.utilizado_cliente.is_(False),
                    Movimentacao.prazo_devolucao != None,
                    Movimentacao.prazo_devolucao < date.today()
                )
            )
        elif status_filtro == "pendente":
            query = query.filter(
                and_(
                    Movimentacao.devolvido.is_(False),
                    Movimentacao.utilizado_cliente.is_(False),
                    or_(
                        Movimentacao.prazo_devolucao == None,
                        Movimentacao.prazo_devolucao >= date.today()
                    )
                )
            )
        elif status_filtro in ("finalizado",): 
            query = query.filter(
                or_(
                    Movimentacao.devolvido.is_(True),
                    Movimentacao.utilizado_cliente.is_(True)
                )
            )

    if data_inicio:
        try:
            dt_inicio = datetime.strptime(data_inicio, "%Y-%m-%d")
            query = query.filter(Movimentacao.data_retirada >= dt_inicio)
        except ValueError:
            flash("Formato de data início inválido.", "error")
    if data_fim:
        try:
            dt_fim = datetime.strptime(data_fim, "%Y-%m-%d")
            dt_fim = dt_fim.replace(hour=23, minute=59, second=59)
            query = query.filter(Movimentacao.data_retirada <= dt_fim)
        except ValueError:
            flash("Formato de data fim inválido.", "error")

    movimentacoes = query.distinct().all()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                            rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    elements = []
    styles = getSampleStyleSheet()

    logo_path = os.path.join(os.path.dirname(__file__), 'static/assets/logo-valltech.png')
    logo = Image(logo_path, width=50*mm, height=30*mm)
    titulo = Paragraph("Relatório de Movimentações", styles["Title"])
    header_table = Table([[logo, titulo]], colWidths=[60*mm, 400*mm])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
    ]))
    elements.append(header_table)

    data = [
        ["Material", "Qtd", "Qtd OK", "Qtd NÃO OK", "Ficou Cliente",
         "Funcionário", "Cliente", "OS", "Retirada", "Prazo", "Status"]
    ]

    for mov in movimentacoes:
        if mov.materiais:
            for mov_mat in mov.materiais:
                material = mov_mat.material
                qtd_total = mov_mat.quantidade or 0

                if mov.devolvido or mov.utilizado_cliente:
                    qtd_ok = mov_mat.quantidade_ok if mov_mat.quantidade_ok is not None else 0
                    qtd_ficou = mov_mat.quantidade_sem_retorno if mov_mat.quantidade_sem_retorno is not None else 0
                    qtd_nok = qtd_total - qtd_ok - qtd_ficou

                    qtd_ok_str = str(qtd_ok)
                    qtd_nok_str = str(qtd_nok)
                    qtd_ficou_str = str(qtd_ficou)
                else:
                    qtd_ok_str = "-"
                    qtd_nok_str = "-"
                    qtd_ficou_str = "-"

                if mov.devolvido:
                    status_formatado = "Devolvido"
                elif mov.utilizado_cliente:
                    status_formatado = "Ficou no Cliente"
                elif mov.prazo_devolucao and mov.prazo_devolucao < date.today():
                    status_formatado = "Atrasado"
                else:
                    status_formatado = "Pendente"

                data.append([
                    material.nome if material else "-",
                    str(qtd_total),
                    qtd_ok_str,
                    qtd_nok_str,
                    qtd_ficou_str,
                    mov.funcionario or "-",
                    mov.cliente.nome if mov.cliente else "-",
                    mov.ordem_servico or "-",
                    mov.data_retirada.strftime("%d/%m/%Y %H:%M") if mov.data_retirada else "-",
                    mov.prazo_devolucao.strftime("%d/%m/%Y") if mov.prazo_devolucao else "-",
                    status_formatado
                ])
        else:
            if mov.devolvido:
                status_formatado = "Devolvido"
            elif mov.utilizado_cliente:
                status_formatado = "Ficou no Cliente"
            elif mov.prazo_devolucao and mov.prazo_devolucao < date.today():
                status_formatado = "Atrasado"
            else:
                status_formatado = "Pendente"

            data.append([
                "-", "", "", "", "",
                mov.funcionario or "-",
                mov.cliente.nome if mov.cliente else "-",
                mov.ordem_servico or "-",
                mov.data_retirada.strftime("%d/%m/%Y %H:%M") if mov.data_retirada else "-",
                mov.prazo_devolucao.strftime("%d/%m/%Y") if mov.prazo_devolucao else "-",
                status_formatado
            ])

    col_widths = [
        45*mm, 12*mm, 15*mm, 18*mm, 20*mm,
        30*mm, 35*mm, 20*mm, 28*mm, 25*mm, 20*mm
    ]

    table = Table(data, repeatRows=1, colWidths=col_widths)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ff7b00")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("FONTSIZE", (0, 1), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("WORDWRAP", (0, 0), (-1, -1), True),
    ]))

    elements.append(table)
    doc.build(elements)

    buffer.seek(0)
    if not movimentacoes:
        flash("Não há movimentações para exportar com os filtros aplicados.", "info")

    return send_file(
        buffer,
        as_attachment=True,
        download_name="movimentacoes.pdf",
        mimetype="application/pdf"
    )

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

    valor =Decimal(request.form["valor"])
    acao = request.form["acao"]

    if acao == "adicionar":
        material.quantidade += valor
    elif acao == "remover":
        material.quantidade = max(material.quantidade - valor, 0)

    db.commit()
    flash("Estoque atualizado com sucesso!", "success")
    return redirect(url_for("estoque.controle"))


@estoque_bp.route("/estoque/export/excel")
def exportar_excel():
    filtro = request.args.get("filtro", "").strip()

    query = db.query(Material)

    if filtro:
        query = query.filter(Material.nome.ilike(f"%{filtro}%"))

    materiais = query.all()

    data = []
    for mat in materiais:
        data.append({
            "Material": mat.nome,
            "Lote": mat.lote or "Sem lote",
            "Quantidade": mat.quantidade,
            "Estoque Mínimo Seco": mat.estoque_minimo_seco,
            "Diferença Seco": mat.quantidade - mat.estoque_minimo_seco,
            "Estoque Mínimo Chuva": mat.estoque_minimo_chuva,
            "Diferença Chuva": mat.quantidade - mat.estoque_minimo_chuva,
        })

    if not data:
        flash("Não há materiais para exportar com o filtro aplicado.", "info")

    df = pd.DataFrame(data)
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Estoque")

    output.seek(0)
    return send_file(
        output,
        as_attachment=True,
        download_name="estoque.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@estoque_bp.route("/estoque/export/pdf")
def exportar_pdf():
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import landscape, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet

    filtro = request.args.get("filtro", "").strip()

    query = db.query(Material)
    if filtro:
        query = query.filter(Material.nome.ilike(f"%{filtro}%"))

    materiais = query.all()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), leftMargin=20, rightMargin=20, topMargin=20, bottomMargin=20)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("Relatório de Estoque", styles["Title"]))
    elements.append(Paragraph(" ", styles["Normal"]))

    data = [
        ["Material", "Lote", "Qtd", "Mínimo Seco", "Dif. Seco", "Mínimo Chuva", "Dif. Chuva"]
    ]

    for mat in materiais:
        data.append([
            mat.nome,
            mat.lote or "Sem lote",
            str(mat.quantidade),
            str(mat.estoque_minimo_seco),
            str(mat.quantidade - mat.estoque_minimo_seco),
            str(mat.estoque_minimo_chuva),
            str(mat.quantidade - mat.estoque_minimo_chuva),
        ])

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ff7b00")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
    ]))
    elements.append(table)
    doc.build(elements)

    buffer.seek(0)
    if not materiais:
        flash("Não há materiais para exportar com o filtro aplicado.", "info")

    return send_file(
        buffer,
        as_attachment=True,
        download_name="estoque.pdf",
        mimetype="application/pdf"
    )

app.register_blueprint(estoque_bp)

@app.route("/colaboradores/novo", methods=["POST"])
def novo_colaborador():
    nome = request.form.get("nome", "").strip()
    if not nome:
        return "Nome inválido", 400

    colaborador_existente = db.query(Colaborador).filter_by(nome=nome).first()
    if colaborador_existente:
        return "Já existe", 400

    novo = Colaborador(nome=nome)
    db.add(novo)
    db.commit()

    return "OK", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
