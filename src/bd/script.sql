CREATE DATABASE estoque_db CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE estoque_db;

CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    senha VARCHAR(255) NOT NULL, 
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE clientes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE materiais (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    quantidade INT NOT NULL DEFAULT 0,
    lote VARCHAR(50),
    estoque_minimo_chuva INT DEFAULT 0,
    estoque_minimo_seco INT DEFAULT 0,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE movimentacoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    material_id INT NOT NULL,
    quantidade INT NOT NULL,
    cliente_id INT,
    ordem_servico VARCHAR(50),
    funcionario VARCHAR(100) NOT NULL, 
    responsavel_id INT NOT NULL,
    data_retirada TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    prazo_devolucao DATE,
    motivo ENUM('manutenção','preventiva','teste','instalação'),
    status ENUM('verde','amarelo','vermelho') DEFAULT 'amarelo',
    devolvido BOOLEAN DEFAULT FALSE,
    utilizado_cliente BOOLEAN DEFAULT FALSE,
    funcionando BOOLEAN,
    observacao TEXT,
    
	CONSTRAINT fk_mov_material FOREIGN KEY (material_id) REFERENCES materiais(id) ON DELETE CASCADE,
    CONSTRAINT fk_mov_cliente FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE SET NULL,
    CONSTRAINT fk_mov_responsavel FOREIGN KEY (responsavel_id) REFERENCES usuarios(id) ON DELETE CASCADE
    );
    
select * from usuarios where id = 1;
select * from clientes where id = 1;
select * from movimentacoes where id = 1;
select * from materiais where id = 1;
