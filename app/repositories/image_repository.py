from app.database import get_connection
from app.models.image import Image


class ImageRepository:
    def _row_to_image(self, row) -> Image:
        return Image(
            id=row["id"],
            image_path=row["image_path"],
            image_type=row["image_type"],
            hash=row["hash"],
        )

    def create_image(self, image: Image) -> Image:
        with get_connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO images (
                    image_path,
                    image_type,
                    hash
                )
                VALUES (?, ?, ?)
                """,
                (
                    image.image_path,
                    image.image_type,
                    image.hash,
                ),
            )

            connection.commit()
            image.id = cursor.lastrowid

            return image

    def get_image_by_id(self, image_id: int) -> Image | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT
                    id,
                    image_path,
                    image_type,
                    hash
                FROM images
                WHERE id = ?
                """,
                (image_id,),
            ).fetchone()

            if row is None:
                return None

            return self._row_to_image(row)

    def delete_image(self, image_id: int) -> bool:
        with get_connection() as connection:
            cursor = connection.execute(
                """
                DELETE FROM images
                WHERE id = ?
                """,
                (image_id,),
            )

            connection.commit()

            return cursor.rowcount > 0
