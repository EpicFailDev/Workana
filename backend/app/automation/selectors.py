"""
Seletores CSS para o scraper do Workana.
Centraliza as strings de busca para facilitar manutenção.
"""


class WorkanaSelectors:
    """Seletores CSS para elementos do Workana."""

    # Listagem de projetos
    PROJECT_CARD = '.project-item, .job-item, [data-testid="project-card"]'
    CARD_TITLE = (
        'a[href*="/job/"], h2.project-title a, h3.project-title a, .project-title a, h2 a, h3 a'
    )
    CARD_DESCRIPTION = ".project-body .html-desc, .html-desc, .project-details, .expander, [data-text-expand], .project-item-description, .project-description"
    CARD_BUDGET = ".values, .budget, .price, span.budget, div.budget"
    CARD_SKILLS = ".skills .skill, .skills .tag, .skills a, .tech-stack .tag, .skill, .tag"
    CARD_PROPOSALS = ".proposals-count, .bids, span.bids"
    CARD_DATE = ".date, time, .project-main-details .date, h5[title]"
    PAGINATION_NEXT = ".pagination .next, a.next"

    # Detalhes do projeto (/job/{slug})
    DETAILS_TITLE = 'h1.title, h1.h3, h1, .project-title, [data-testid="project-title"]'
    DETAILS_DESCRIPTION = '.block-detail .specification .expander, .block-detail .expander, .expander, .project-details, .job-details, .job-description, div[data-testid="job-description"], .project-body, .description, .project-description, #project-details'
    DETAILS_BUDGET = "h4.budget, .values, .budget, .price, span.budget, div.budget"
    DETAILS_SKILLS = ".skills .skill, .skills a, .skills .tag, .tech-stack .tag, ul.skills li, .skills span, .skill, .tag"
    DETAILS_CLIENT_NAME = ".user-name span, .user-name, .wk-user-info .user-name, .client-name, .employer-name, .client-info h4, .project-author a, .profile-name"
    DETAILS_CLIENT_COUNTRY = (
        ".wk-user-info .country .flag, .client-country, .location, .country, .country-name"
    )
    DETAILS_RATING = ".profile-stars .stars-bg, .stars-container, .rating, .score, .rating-box"
    DETAILS_SIDEBAR = "aside, .project-details-sidebar, #sidebar, .employer-history, .wk-user-info"
    DETAILS_STARS = ".fa-star"

    # Formulário de Proposta / Bid Form (Mapeados diretamente via Engenharia Reversa do bundle.1398 e HAR real)
    BID_BUTTON = '.bid-button, a[href*="/messages/bid/"], a:has-text("Fazer uma proposta"), a:has-text("Make bid"), a:has-text("Enviar proposta")'
    BID_FORM = '#bidForm, form[action*="/messages/bid/"], form'
    BID_AMOUNT_INPUT = '#Amount, input[name="bid[amount]"], input#Amount, #WorkerNetAmount, input[name="bid[workerNetAmount]"]'
    BID_NET_AMOUNT_INPUT = '#WorkerNetAmount, input[name="bid[workerNetAmount]"]'
    BID_HOURS_INPUT = '#Hours, #WorkHours, input[name="bid[hours]"]'
    BID_MESSAGE_TEXTAREA = '#BidContent, textarea[name="bid[content]"], textarea#bid_content, textarea.bid-content, textarea[name="bid_message"], .fr-element, div[contenteditable="true"]'
    BID_DELIVERY_TIME_INPUT = '#BidDeliveryTime, input[name="bid[deliveryTime]"], select[name="bid[deliveryTime]"], select#BidDeliveryTime'
    BID_DELIVERY_TIME_SELECT = '#BidDeliveryTime, input[name="bid[deliveryTime]"], select[name="bid[deliveryTime]"], select#BidDeliveryTime'
    BID_QUESTION_INPUTS = '#projectQuestions textarea, .project-questions textarea, .bid-form-question textarea, textarea[name^="project_questions"], textarea[name*="question" i], input[name^="project_questions"]'
    BID_ACKNOWLEDGE_CHECKBOX = 'input[name="acknowledged"], input#acknowledged, input[type="checkbox"][name*="terms" i], input[type="checkbox"][name*="agree" i]'
    BID_SUBMIT_BUTTON = '.wk-submit-block button[type="submit"], button.btn-primary[type="submit"], #btn-submit-bid, button[type="submit"]:has-text("Enviar"), button[type="submit"]:has-text("Send"), button:has-text("Enviar proposta"), button:has-text("Fazer proposta")'
    BID_SUPER_BIDS_MODAL_SKIP = 'button:has-text("Send without extras"), button:has-text("Enviar sem extras"), button:has-text("Enviar sin extras"), button:has-text("Não, obrigado"), button:has-text("No, thanks"), a:has-text("Enviar sem extras"), a:has-text("Send without extras")'
    BID_ALERT_CONFIRM_BUTTON = '.modal button:has-text("Continuar"), .modal button:has-text("Continue"), .modal button:has-text("OK"), .modal button:has-text("Entendi"), .modal button:has-text("Confirmar"), .modal button:has-text("Confirm"), .modal button:has-text("Sim")'

    # Tokens de Segurança (CSRF/DCST) — Descobertos via análise HAR real
    CSRF_VALUE_INPUT = 'input[name="csrf_value"]'
    CSRF_NAME_INPUT = 'input[name="csrf_name"]'
    DCST_INPUT = 'input[name="dcst-input"]'
    TURNSTILE_RESPONSE_INPUT = 'input[name="cf-turnstile-response"]'
    TURNSTILE_WIDGET = ".cf-turnstile, div[data-sitekey]"

    # Skills Checkboxes no formulário de proposta (HAR: skill-flutter=flutter, skill-api=api)
    BID_SKILL_CHECKBOXES = 'input[name^="skill-"], input[type="checkbox"][name^="skill"]'

    # Validação pós-submit — O redirect de sucesso contém estes parâmetros
    # Ex: /messages/index/{slug}/{user}?added=214932899&bid=1&isFromInbox=0
    POST_SUBMIT_SUCCESS_PARAMS = ("added=", "bid=1")

    # ── APIs internas do Workana (descobertas via HAR) ──
    RECOMMENDED_PROJECTS_ENDPOINT = "/dashboard/recommended_projects"
    SAVED_SEARCHES_ENDPOINT = "/saved_searches/1"
    CHAT_FRIENDS_ENDPOINT = "/chat/friends"
    NOTIFICATIONS_ENDPOINT = "/notifications"
    THREADS_ATTACHMENTS_ENDPOINT = "/threads/{thread_id}/attachments"
    UPLOAD_ASSEMBLIES_ENDPOINT = "https://upload.workana.com/upload/assemblies"
