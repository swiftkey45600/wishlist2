from app.database import get_connection
from app.models.marketplace import Marketplace


class MarketplacesLinksRepository:
    def _row_to_marketplace(self, row) -> Marketplace:
        return Marketplace(
            id=row["id"],
            slug=row["slug"],
            name=row["name"],
            base_url=row["base_url"],
            logo_url=row["logo_url"],
        )

    def get_all(self) -> list[Marketplace]:
        with get_connection() as connection:
            rows = connection.execute(
                "SELECT id, slug, name, base_url, logo_url FROM marketplaces"
            ).fetchall()
            return [self._row_to_marketplace(row) for row in rows]

    def get_by_slug(self, slug: str) -> Marketplace | None:
        with get_connection() as connection:
            row = connection.execute(
                "SELECT id, slug, name, base_url, logo_url FROM marketplaces WHERE slug = ?",
                (slug,),
            ).fetchone()
            if row is None:
                return None
            return self._row_to_marketplace(row)

    def create(self, marketplace: Marketplace) -> Marketplace:
        with get_connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO marketplaces (slug, name, base_url, logo_url)
                VALUES (?, ?, ?, ?)
                """,
                (marketplace.slug, marketplace.name, marketplace.base_url, marketplace.logo_url),
            )
            connection.commit()
            marketplace.id = cursor.lastrowid
            return marketplace

    def delete(self, slug: str) -> bool:
        with get_connection() as connection:
            cursor = connection.execute(
                "DELETE FROM marketplaces WHERE slug = ?", (slug,)
            )
            connection.commit()
            return cursor.rowcount > 0