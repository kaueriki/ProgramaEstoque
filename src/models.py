from sqlalchemy import (
    create_engine, Column, Integer, String, Boolean, Text, Date, DateTime, ForeignKey, Enum, DECIMAL
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime, date
from urllib.parse import quote_plus

DB_USER = "root"
DB_PASSWORD = quote_plus("@vall1717")
DB_HOST = "127.0.0.1"
DB_PORT = "3306"
DB_NAME = "estoque_db"

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL, echo=True)
Base = declarative_base()


class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=False)
    senha = Column(String(255), nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow)


class Cliente(Base):
    __tablename__ = "clientes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(150), nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow)


class Material(Base):
    __tablename__ = "materiais"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(150), nullable=False)
    quantidade = Column(DECIMAL(10, 2), nullable=False, default=0.00)
    unidade_medida = Column(String(20), nullable=False, default="unidade")
    lote = Column(String(50))
    estoque_minimo_chuva = Column(DECIMAL(10, 2), default=0.00)
    estoque_minimo_seco = Column(DECIMAL(10, 2), default=0.00)
    criado_em = Column(DateTime, default=datetime.utcnow)


class Movimentacao(Base):
    __tablename__ = "movimentacoes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"))
    ordem_servico = Column(String(50))
    funcionario = Column(String(100), nullable=False)
    responsavel_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    data_retirada = Column(DateTime, default=datetime.utcnow)
    prazo_devolucao = Column(Date)
    motivo = Column(Enum("manutenção", "emprestimo", "feira", "teste", "instalação", "preventiva", "montagem"), nullable=True)
    status = Column(Enum("verde", "amarelo", "vermelho"), default="amarelo")
    devolvido = Column(Boolean, default=False)
    utilizado_cliente = Column(Boolean, default=False)
    funcionando = Column(Boolean, default=True)
    observacao = Column(Text)

    cliente = relationship("Cliente")
    responsavel = relationship("Usuario")
    materiais = relationship(
        "MovimentacaoMaterial",
        back_populates="movimentacao",
        cascade="all, delete-orphan"
    )

    @property
    def status_atual(self):
        if self.devolvido:
            return "Devolvido"
        if self.utilizado_cliente:
            return "Ficou no Cliente"
        if self.prazo_devolucao and self.prazo_devolucao < date.today():
            return "Atrasado"
        return "Pendente"


class MovimentacaoMaterial(Base):
    __tablename__ = "movimentacoes_materiais"
    id = Column(Integer, primary_key=True, autoincrement=True)
    movimentacao_id = Column(Integer, ForeignKey("movimentacoes.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materiais.id"), nullable=False)
    quantidade = Column(DECIMAL(10, 2), nullable=False)
    quantidade_ok = Column(DECIMAL(10, 2), nullable=True, default=None)
    quantidade_sem_retorno = Column(DECIMAL(10, 2), nullable=True, default=None)


    movimentacao = relationship("Movimentacao", back_populates="materiais")
    material = relationship("Material")


class Colaborador(Base):
    __tablename__ = "colaboradores"

    id = Column(Integer, primary_key=True)
    nome = Column(String(100), unique=True, nullable=False)

    def __repr__(self):
        return f"<Colaborador(nome={self.nome})>"

Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()


# novo_usuario = Usuario(
#     nome="admin",
#     senha="1234"
# )
# session.add(novo_usuario)
# session.commit()

# novo_cliente = Cliente(nome="Ceagesp")
# session.add(novo_cliente)

# novo_material1 = Material(nome="Parafuso 10mm", quantidade=100, lote="1", estoque_minimo_chuva=50, estoque_minimo_seco=30)
# novo_material2 = Material(nome="Porca 10mm", quantidade=150, lote="2", estoque_minimo_chuva=40, estoque_minimo_seco=20)
# session.add_all([novo_material1, novo_material2])
# session.commit()

# nova_movimentacao = Movimentacao(
#     cliente_id=1,
#     ordem_servico="43000",
#     funcionario="Bidu",
#     responsavel_id=1,
#     prazo_devolucao=date(2025, 9, 10),
#     motivo="manutenção",
#     status="amarelo",
#     devolvido=False,
#     utilizado_cliente=True,
#     funcionando=True,
#     observacao="Material entregue em bom estado."
# )
# session.add(nova_movimentacao)
# session.flush()  # Para gerar o ID da movimentação

# # Adiciona os materiais na movimentação
# mov_mat1 = MovimentacaoMaterial(movimentacao_id=nova_movimentacao.id, material_id=1, quantidade=10)
# mov_mat2 = MovimentacaoMaterial(movimentacao_id=nova_movimentacao.id, material_id=2, quantidade=20)
# session.add_all([mov_mat1, mov_mat2])

# # Atualiza o estoque dos materiais
# mat1 = session.query(Material).get(1)
# mat2 = session.query(Material).get(2)
# mat1.quantidade -= 10
# mat2.quantidade -= 20

# session.commit()
