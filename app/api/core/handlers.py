from app.api.core.process import OptimizationProcess
from app.common.enums.optimization_enum import TypeOptimizationEnum

class OptimizationHandler:

    @staticmethod
    async def create(payload):
        return await OptimizationProcess().create(payload)

    @staticmethod
    async def list():
        return await OptimizationProcess().list()

    @staticmethod
    async def get(optimization_type: TypeOptimizationEnum, process_uuid: str):
        return await OptimizationProcess().get(optimization_type, process_uuid)

    @staticmethod
    async def update(process_uuid: str, payload):
        return await OptimizationProcess().update(process_uuid, payload)

    @staticmethod
    async def delete(process_uuid: str):
        return await OptimizationProcess().delete(process_uuid)
    