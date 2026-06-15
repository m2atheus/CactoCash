CREATE TABLE IF NOT EXISTS despesa (
    id SERIAL PRIMARY KEY,
    descricao VARCHAR(255) NOT NULL,
    valor DECIMAL(10, 2) NOT NULL CHECK (valor > 0),
    data_vencimento DATE NOT NULL,
    data_pagamento DATE,
    categoria_id INTEGER NOT NULL REFERENCES categoria(id),
    forma_pagamento VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('pago', 'pendente', 'atrasado')),
    observacoes TEXT,
    usuario_id INTEGER REFERENCES users(id),
    recorrente BOOLEAN DEFAULT FALSE,
    data_fim_recorrencia DATE,
    comprovante TEXT
);

CREATE INDEX IF NOT EXISTS idx_despesa_usuario ON despesa(usuario_id);
CREATE INDEX IF NOT EXISTS idx_despesa_vencimento ON despesa(data_vencimento);
