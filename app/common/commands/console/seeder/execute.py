import os
import re
import json
import importlib
from datetime import datetime, timezone

from beanie import Document

from app.common.models.seeder_model import SeederModel


class Execute:
    def __init__(self):
        self.files_data = []
        self.base_path = os.getcwd()
        self.base_relative_path = "database/seeders"
        self.base_module = self.base_relative_path.replace("/", ".")

    async def run(self, product_name=None):
        await self._set_latest_batch()
        product = product_name if product_name else os.environ.get('PRODUCT')

        if not product:
            return "No product was configured in env"

        self._load_files_from_path(product)

        for file_data in self.files_data:
            await self._process_file(file_data)

        return "Done!"

    async def _set_latest_batch(self):
        latest_record = await SeederModel.find().sort("-batch").first_or_none()
        self.batch = 1 if latest_record is None else latest_record.batch + 1

    def _load_files_from_path(self, relative_path: str):
        base_path = os.path.join(
            self.base_path, self.base_relative_path, relative_path
        )

        if os.path.isdir(base_path):
            self.files_data = [
                self._get_file_data(file, relative_path)
                for file in sorted(os.listdir(base_path))
                if os.path.isfile(os.path.join(base_path, file))
            ]

    def _get_file_data(self, filename: str, relative_path: str):
        name, _ = os.path.splitext(filename)
        return name, f"{self.base_module}.{relative_path}.{name}"

    async def _process_file(self, file_data):
        filename, json_path = file_data

        model_name = re.sub(r"^\d+_", "", filename)
        model = self._get_model_class(model_name)

        if model:
            name_batch = f"{filename}_v{self.batch}"
            existing_seed = await SeederModel.find_by_name(name_batch)

            if not existing_seed:
                await self._insert_json_data(json_path, model, self.batch)
                await SeederModel(seed=name_batch, batch=self.batch).insert()

    def _get_model_class(self, model_name: str):
        """Return the model class based on the file name."""
        try:
            class_name = ''.join(
                word.capitalize() for word in model_name.split('_')
            )
            models_module = importlib.import_module(
                f"app.common.models.{model_name}"
            )

            return getattr(models_module, class_name, None)
        except ModuleNotFoundError:
            return None

    async def _insert_json_data(
        self,
        json_path: str,
        model: Document,
        version: int
    ):
        """Insert JSON data into the model's collection."""
        try:
            path = f"{self.base_path}/{json_path.replace('.', '/')}.json"

            await self._soft_delete_existing_records(model)

            with open(path, 'r', encoding='utf-8-sig') as json_file:
                data = json.load(json_file)
                if isinstance(data, list):
                    data = [
                        model(**{**item, 'version': version}) for item in data
                    ]
                    await model.insert_many(data)
                else:
                    data['version'] = version
                    await model(**data).insert()


        except FileNotFoundError:
            print(f"File not found: {path}")
        except Exception as e:
            print(f"Error inserting data from {path}: {e}")

    async def _soft_delete_existing_records(self, model: Document):
        """Soft delete all records from the model by setting 'deleted_at'."""
        try:
            existing_records = await model.find({"deleted_at": None}).to_list()
            for record in existing_records:
                record.deleted_at = datetime.now(timezone.utc)
                await record.save()

        except Exception as e:
            print(f"Error soft deleting existing records: {e}")
