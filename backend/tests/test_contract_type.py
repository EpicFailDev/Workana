from app.services.contract_type import detect_contract_type


def test_fixed_default():
    assert detect_contract_type(title="Desenvolvimento de site", description="Escopo fechado") == "project_fixed"


def test_hourly_budget():
    assert detect_contract_type(budget_type="hourly", title="Manutenção") == "hourly"
    assert detect_contract_type(budget_type="hora", description="Suporte") == "hourly"


def test_fixed_budget():
    assert detect_contract_type(budget_type="fixed", title="Landing page") == "project_fixed"


def test_hourly_text_signal():
    assert detect_contract_type(title="Suporte mensal", description="Pagamento por hora") == "hourly"
    assert detect_contract_type(title="Tarefas", description="Taxa horária de R$ 50") == "hourly"


def test_staff_augmentation_signal():
    assert detect_contract_type(
        title="Dedicated developer",
        description="Buscamos staff augmentation para compor o time",
    ) == "staff_augmentation"
    assert detect_contract_type(
        description="Quero integrar a time e pagar por hora",
    ) == "staff_augmentation"


def test_none_inputs_safe():
    assert detect_contract_type() == "project_fixed"
    assert detect_contract_type(title=None, description=None, budget_type=None) == "project_fixed"