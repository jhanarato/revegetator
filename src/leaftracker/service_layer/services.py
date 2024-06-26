from leaftracker.domain.model import Source, SourceType, Batch, BatchType, Species
from leaftracker.service_layer.unit_of_work import UnitOfWork


class ServiceError(RuntimeError):
    pass


class InvalidSource(Exception):
    pass


def add_nursery(name: str, uow: UnitOfWork):
    with uow:
        source = Source(name, SourceType.NURSERY)
        uow.sources().add(source)
        uow.commit()


def add_program(name: str, uow: UnitOfWork):
    with uow:
        source = Source(name, SourceType.PROGRAM)
        uow.sources().add(source)
        uow.commit()


def _add_batch(source_name: str, batch_type: BatchType, uow: UnitOfWork) -> str:
    with uow:
        source = uow.sources().get(source_name)

        if not source:
            raise InvalidSource(f"No such source: {source_name}")

        batchref = uow.batches().add(
            Batch(
                source=source,
                batch_type=batch_type
            )
        )
        uow.commit()

    return batchref


def add_order(source_name: str, uow: UnitOfWork) -> str:
    return _add_batch(source_name, BatchType.ORDER, uow)


def add_delivery(source_name: str, uow: UnitOfWork) -> str:
    return _add_batch(source_name, BatchType.DELIVERY, uow)


def add_pickup(source_name: str, uow: UnitOfWork) -> str:
    return _add_batch(source_name, BatchType.PICKUP, uow)


def add_species(current_name: str, uow: UnitOfWork) -> str:
    species = Species(current_name)

    with uow:
        uow.species().add(species)
        uow.commit()

    if species.reference is None:
        raise ServiceError("Committed species was not assigned a reference.")

    return species.reference


def rename_species(reference: str, name: str, uow: UnitOfWork) -> None:
    with uow:
        species = uow.species().get(reference)

        if species is None:
            raise ServiceError(f"No species for reference {reference}.")

        species.taxon_history.new_current_name(name)
        uow.commit()
