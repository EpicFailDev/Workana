import React from 'react';
import { Plus, Ban, Trash2 } from 'lucide-react';
import styles from '../../pages/Settings.module.css';
import type { BlacklistedClient } from '../../services/api';

interface BlacklistTabProps {
  blacklist: BlacklistedClient[];
  newClientName: string;
  setNewClientName: React.Dispatch<React.SetStateAction<string>>;
  newClientReason: string;
  setNewClientReason: React.Dispatch<React.SetStateAction<string>>;
  handleAddBlacklist: () => void;
  isAddingBlacklist: boolean;
  handleRemoveBlacklist: (id: number) => void;
}

export const BlacklistTab: React.FC<BlacklistTabProps> = ({
  blacklist,
  newClientName,
  setNewClientName,
  newClientReason,
  setNewClientReason,
  handleAddBlacklist,
  isAddingBlacklist,
  handleRemoveBlacklist,
}) => {
  return (
    <div className={styles.animated}>
      <h2 className={styles.sectionTitle}>Lista Negra de Clientes</h2>
      <p className={styles.sectionSubtitle}>
        Projetos destes clientes serão desconsiderados automaticamente pela automação
      </p>

      {/* Adicionar à Lista Negra */}
      <div className={styles.card}>
        <h3
          className="text-lg font-bold mb-4"
          style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
        >
          <Plus size={20} />
          Bloquear Novo Cliente
        </h3>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr auto',
            gap: '12px',
            alignItems: 'flex-end',
          }}
        >
          <div>
            <label className={styles.label}>Nome do Cliente ou Usuário</label>
            <input
              type="text"
              className={styles.input}
              placeholder="Ex: Empresa XYZ ou @usuario123"
              value={newClientName}
              onChange={(e) => setNewClientName(e.target.value)}
            />
          </div>

          <div>
            <label className={styles.label}>Motivo do Bloqueio (Opcional)</label>
            <input
              type="text"
              className={styles.input}
              placeholder="Ex: Não responde, orçamento irreal, spam"
              value={newClientReason}
              onChange={(e) => setNewClientReason(e.target.value)}
            />
          </div>

          <button
            className="btn btn-primary"
            onClick={handleAddBlacklist}
            disabled={isAddingBlacklist || !newClientName.trim()}
            style={{
              height: '42px',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <Ban size={16} />
            {isAddingBlacklist ? 'Bloqueando...' : 'Bloquear'}
          </button>
        </div>
      </div>

      {/* Tabela de Bloqueados */}
      <div className={styles.card}>
        <h3 className="text-lg font-bold mb-3">Clientes Bloqueados ({blacklist.length})</h3>

        {blacklist.length === 0 ? (
          <p
            style={{
              color: 'var(--color-text-muted)',
              fontSize: '0.9rem',
              padding: '16px 0',
            }}
          >
            Nenhum cliente bloqueado até o momento.
          </p>
        ) : (
          <div className={styles.tableContainer}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Cliente</th>
                  <th>Motivo</th>
                  <th>Data</th>
                  <th style={{ textAlign: 'right' }}>Ação</th>
                </tr>
              </thead>
              <tbody>
                {blacklist.map((item) => (
                  <tr key={item.id}>
                    <td style={{ fontWeight: 600 }}>{item.client_name}</td>
                    <td style={{ color: 'var(--color-text-secondary)' }}>
                      {item.reason || 'Sem motivo registrado'}
                    </td>
                    <td
                      style={{
                        color: 'var(--color-text-muted)',
                        fontSize: '0.8rem',
                      }}
                    >
                      {new Date(item.created_at).toLocaleDateString('pt-BR')}
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <button
                        className="btn btn-ghost btn-sm"
                        onClick={() => handleRemoveBlacklist(item.id)}
                        title="Desbloquear cliente"
                        style={{ color: '#ef4444', padding: '4px 8px' }}
                      >
                        <Trash2 size={16} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
