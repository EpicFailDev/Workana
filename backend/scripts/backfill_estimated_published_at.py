"""
Backfill das colunas normalizadas do catálogo introduzidas na migration
20260820000000_bids_history_and_est_published.sql:

  - estimated_published_at: calculado a partir de `posted_at` (texto relativo
    do Workana) usando `last_seen_at` da linha como referência temporal (o
    texto "há X horas" foi resolvido na captura).
  - contract_type: detectado a partir de budget_type/título/descrição, somente
    quando a linha ainda está no default ('project_fixed') para não sobrescrever
    classificações existentes.

Uso:  python -m scripts.backfill_estimated_published_at   (a partir de backend/)
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select, update

from app.database import crud
from app.database.models import ProjectCatalog as ProjectCatalogModel
from app.services.dates import parse_relative_datetime
from app.services.contract_type import detect_contract_type


async def backfill_estimated_published_at(batch_size: int = 200) -> dict:
    updated_est = 0
    reclassified = 0
    scanned = 0

    while True:
        async with crud.async_session() as session:
            result = await session.execute(
                select(ProjectCatalogModel)
                .where(ProjectCatalogModel.estimated_published_at.is_(None))
                .limit(batch_size)
            )
            rows = result.scalars().all()
        if not rows:
            break

        progress = 0
        for row in rows:
            scanned += 1
            value = parse_relative_datetime(row.posted_at, base_time=row.last_seen_at)
            if value is None:
                continue
            async with crud.async_session() as session:
                await session.execute(
                    update(ProjectCatalogModel)
                    .where(ProjectCatalogModel.workana_id == row.workana_id)
                    .values(estimated_published_at=value)
                )
                await session.commit()
            updated_est += 1
            progress += 1

        # Nenhuma linha do lote pôde ser resolvida -> não há mais o que fazer.
        if progress == 0:
            break

    # Backfill de contract_type apenas para linhas ainda no default
    async with crud.async_session() as session:
        result = await session.execute(
            select(ProjectCatalogModel)
            .where(ProjectCatalogModel.contract_type == "project_fixed")
            .limit(batch_size)
        )
        rows = result.scalars().all()
    for row in rows:
        detected = detect_contract_type(
            budget_type=row.budget_type,
            title=row.title,
            description=row.description,
            details=row.details,
        )
        if detected != "project_fixed":
            async with crud.async_session() as session:
                await session.execute(
                    update(ProjectCatalogModel)
                    .where(ProjectCatalogModel.workana_id == row.workana_id)
                    .values(contract_type=detected)
                )
                await session.commit()
            reclassified += 1

    return {"scanned": scanned, "updated_est": updated_est, "reclassified": reclassified}


async def main() -> None:
    stats = await backfill_estimated_published_at()
    print(f"Backfill concluído: {stats}")


if __name__ == "__main__":
    asyncio.run(main())
