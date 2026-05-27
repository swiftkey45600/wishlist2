import hashlib

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

    def _calculate_hash(self, image_path: str) -> str:
        sha256_hash = hashlib.sha256()

        with open(image_path, "rb") as image_file:
            for byte_block in iter(lambda: image_file.read(4096), b""):
                sha256_hash.update(byte_block)

        return sha256_hash.hexdigest()

    def create_image(self, image: Image) -> Image:
        image_hash = self._calculate_hash(image.image_path)

        existing_image = self.get_image_by_hash(image_hash)

        if existing_image is not None:
            raise ValueError("Image already exists")

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
                    image_hash,
                ),
            )

            connection.commit()
            image.id = cursor.lastrowid
            image.hash = image_hash

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

    def get_image_by_hash(self, image_hash: str) -> Image | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT
                    id,
                    image_path,
                    image_type,
                    hash
                FROM images
                WHERE hash = ?
                """,
                (image_hash,),
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
