import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Shield, AlertTriangle } from 'lucide-react';
import { Button } from '../components/ui/button';

export default function Privacidade() {
  const navigate = useNavigate();

  return (
    <div className="flex min-height-screen w-full items-center justify-center p-4 bg-radial from-[#0f1123] to-[#06070d] py-12">
      <div className="w-full max-w-[800px] rounded-3xl border border-white/5 bg-[#0c0c14]/80 p-8 shadow-2xl backdrop-blur-xl relative overflow-hidden animate-slide-up">
        {/* Decorative Top Line */}
        <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-slate-500 via-slate-600 to-slate-700" />

        {/* Back Button */}
        <button
          type="button"
          onClick={() => navigate(-1)}
          className="absolute left-6 top-6 text-slate-400 hover:text-white flex items-center gap-1.5 text-xs transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Voltar
        </button>

        {/* Warning Badge for Legal Review */}
        <div className="mt-8 mb-6 flex items-center gap-3 p-4 bg-amber-500/10 border border-amber-500/20 text-amber-400 rounded-2xl">
          <AlertTriangle className="w-5 h-5 shrink-0" />
          <div className="text-xs leading-normal">
            <span className="font-bold uppercase block">Documento sob Revisão</span>
            Esta política de privacidade está sob revisão jurídica obrigatória antes do lançamento de produção.
          </div>
        </div>

        {/* Header */}
        <div className="flex items-center gap-3 mb-6 pb-6 border-b border-white/5">
          <Shield className="w-8 h-8 text-slate-400" />
          <div>
            <h1 className="text-2xl font-extrabold text-white">Política de Privacidade</h1>
            <p className="text-xs text-slate-400">Última atualização: Junho de 2026 (Versão Preliminar)</p>
          </div>
        </div>

        {/* Legal Text */}
        <div className="space-y-6 text-sm text-slate-300 max-h-[400px] overflow-y-auto pr-2 scrollbar">
          <section className="space-y-2">
            <h2 className="text-base font-bold text-white">1. Informações Coletadas</h2>
            <p className="leading-relaxed">
              Coletamos dados necessários para autenticação e segurança do seu acesso, incluindo endereço de e-mail, logs de acesso ao sistema (data, hora e IP) e tokens criptografados de sessão persistida (usados de acordo com sua preferência no checkbox "Lembrar-me").
            </p>
          </section>

          <section className="space-y-2">
            <h2 className="text-base font-bold text-white">2. Como Utilizamos seus Dados</h2>
            <p className="leading-relaxed">
              Os dados de autenticação são tratados estritamente para:
            </p>
            <ul className="list-disc pl-5 space-y-1 text-slate-400">
              <li>Permitir o login seguro e restaurar suas sessões de uso.</li>
              <li>Prevenir fraudes e acessos não autorizados por meio da autenticação de duplo fator ou envio de códigos OTP.</li>
              <li>Monitorar a estabilidade do sistema e investigar incidentes de segurança.</li>
            </ul>
          </section>

          <section className="space-y-2">
            <h2 className="text-base font-bold text-white">3. Persistência de Tokens de Acesso</h2>
            <p className="leading-relaxed">
              De acordo com a sua escolha no formulário de login:
            </p>
            <ul className="list-disc pl-5 space-y-1 text-slate-400">
              <li>Se a opção "Lembrar-me" for ativada, seu token de sessão será salvo no armazenamento local persistente do navegador (<code className="text-slate-300">localStorage</code>), mantendo seu acesso ativo após fechar o navegador.</li>
              <li>Caso desmarque a opção, o token será mantido apenas na memória temporária da aba ativa (<code className="text-slate-300">sessionStorage</code>) e será removido ao fechar a aba.</li>
            </ul>
          </section>

          <section className="space-y-2">
            <h2 className="text-base font-bold text-white">4. Seus Direitos (LGPD)</h2>
            <p className="leading-relaxed">
              Você possui o direito de confirmar a existência de tratamento de dados pessoais, solicitar acesso a eles, corrigir dados incompletos ou inexatos, ou solicitar a exclusão de sua conta a qualquer momento. Suas solicitações podem ser feitas diretamente por nossos canais corporativos de suporte.
            </p>
          </section>
        </div>

        {/* Action Button */}
        <div className="mt-8 pt-6 border-t border-white/5 flex justify-end">
          <Button
            type="button"
            onClick={() => navigate(-1)}
            className="bg-white/5 hover:bg-white/10 border border-white/10 text-white rounded-xl px-6 h-11"
          >
            Voltar
          </Button>
        </div>
      </div>
    </div>
  );
}
