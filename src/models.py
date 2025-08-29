from sqlalchemy import create_engine, Column, Integer, String, Boolean, Text, Date, DateTime, ForeignKey, Enum
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime

from urllib.parse import quote_plus

DB_USER = "root"
DB_PASSWORD = quote_plus("@vall1717") 
DB_HOST = "localhost"
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
    quantidade = Column(Integer, nullable=False, default=0)
    lote = Column(String(50))
    estoque_minimo_chuva = Column(Integer, default=0)
    estoque_minimo_seco = Column(Integer, default=0)
    criado_em = Column(DateTime, default=datetime.utcnow)


class Movimentacao(Base):
    __tablename__ = "movimentacoes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    material_id = Column(Integer, ForeignKey("materiais.id"), nullable=False)
    quantidade = Column(Integer, nullable=False)
    cliente_id = Column(Integer, ForeignKey("clientes.id"))
    ordem_servico = Column(String(50))
    funcionario = Column(String(100), nullable=False)
    responsavel_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    data_retirada = Column(DateTime, default=datetime.utcnow)
    prazo_devolucao = Column(Date)
    motivo = Column(Enum("manutenção","preventiva","teste","instalação"), nullable=True)
    status = Column(Enum("verde","amarelo","vermelho"), default="amarelo")
    devolvido = Column(Boolean, default=False)
    utilizado_cliente = Column(Boolean, default=False)
    funcionando = Column(Boolean)
    observacao = Column(Text)

    material = relationship("Material")
    cliente = relationship("Cliente")
    responsavel = relationship("Usuario")


Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

print("Banco de dados pronto")

# novo_usuario = Usuario(
#     nome="Teste",
#     senha="1234" 
# )
# session.add(novo_usuario)

# novo_cliente = Cliente(
#     nome="Ceagesp",
# )
# session.add(novo_cliente)

# novo_material = Material(
#     nome="Parafuso 10mm",
#     quantidade=100,
#     lote="1",
#     estoque_minimo_chuva=50,
#     estoque_minimo_seco=30
# )
# session.add(novo_material)

# session.commit()

# print("Usuário, cliente e material inseridos com sucesso ✅")

# nova_movimentacao = Movimentacao(
#     material_id=1,         
#     quantidade=10,
#     cliente_id=1,        
#     ordem_servico="43000",
#     funcionario="Bidu",
#     responsavel_id=1,     
#     prazo_devolucao="2025-09-10",
#     motivo="manutenção",
#     status="amarelo",
#     devolvido=False,
#     utilizado_cliente=True,
#     funcionando=True,
#     observacao="Material entregue em bom estado."
# )

# session.add(nova_movimentacao)
# session.commit()

# print("Movimentação registrada ")
