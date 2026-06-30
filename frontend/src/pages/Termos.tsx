import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Scale, AlertTriangle } from 'lucide-react';
import { Button } from '../components/ui/button';

export default function Termos() {
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
            Esta página pública e seus termos estão sob revisão jurídica obrigatória antes do lançamento de produção.
          </div>
        </div>

        {/* Header */}
        <div className="flex items-center gap-3 mb-6 pb-6 border-b border-white/5">
          <Scale className="w-8 h-8 text-slate-400" />
          <div>
            <h1 className="text-2xl font-extrabold text-white">Termos de Serviço</h1>
            <p className="text-xs text-slate-400">Última atualização: Junho de 2026 (Versão Preliminar)</p>
          </div>
        </div>

        {/* Legal Text */}
        <div className="space-y-6 text-sm text-slate-300 max-h-[400px] overflow-y-auto pr-2 scrollbar">
          <section className="space-y-2">
            <h2 className="text-base font-bold text-white">1. Aceitação dos Termos</h2>
            <p className="leading-relaxed">
              Ao criar uma conta ou utilizar os serviços desta plataforma, você declara e garante que leu, compreendeu e concorda em estar vinculado a estes termos de serviço. Se você não concordar com qualquer disposição aqui estabelecida, não está autorizado a acessar ou utilizar nossa plataforma.
            </p>
          </section>

          <section className="space-y-2">
            <h2 className="text-base font-bold text-white">2. Elegibilidade e Cadastro de Conta</h2>
            <p className="leading-relaxed">
              O acesso a esta plataforma é exclusivo para fins corporativos e comerciais. Ao cadastrar uma conta, você se compromete a fornecer informações verdadeiras, atualizadas e completas, mantendo a confidencialidade absoluta das suas credenciais de acesso, incluindo senha e códigos OTP recebidos.
            </p>
          </section>

          <section className="space-y-2">
            <h2 className="text-base font-bold text-white">3. Uso Autorizado e Restrições</h2>
            <p className="leading-relaxed">
              Você concorda em utilizar a plataforma estritamente de acordo com as leis vigentes e regulamentações do seu país. É expressamente vedado:
            </p>
            <ul className="list-disc pl-5 space-y-1 text-slate-400">
              <li>Utilizar robôs de extração de dados não autorizados na plataforma.</li>
              <li>Tentar violar os sistemas de autenticação ou obter acesso a contas de terceiros.</li>
              <li>Compartilhar credenciais corporativas com indivíduos não autorizados.</li>
            </ul>
          </section>

          <section className="space-y-2">
            <h2 className="text-base font-bold text-white">4. Propriedade Intelectual</h2>
            <p className="leading-relaxed">
              Todos os direitos de propriedade intelectual sobre o software, design de interfaces, marcas e conteúdo gerado pela plataforma pertencem exclusivamente à nossa corporação. Nenhum direito de propriedade intelectual é transferido a você sob estes termos.
            </p>
          </section>

          <section className="space-y-2">
            <h2 className="text-base font-bold text-white">5. Limitação de Responsabilidade</h2>
            <p className="leading-relaxed">
              Na extensão máxima permitida pela lei aplicável, a plataforma é fornecida "como está" e "conforme disponível". Não garantimos que a plataforma estará isenta de interrupções ou erros, tampouco nos responsabilizamos por quaisquer perdas financeiras decorrentes da utilização da nossa ferramenta.
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
