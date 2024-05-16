from typing import Self

import pytest

from leaftracker.adapters.repository import BatchRepository, SourceRepository, SpeciesRepository
from leaftracker.domain.model import Batch, Source, SourceType, BatchType, Stock, StockSize, Species
from leaftracker.service_layer import services
from leaftracker.service_layer.services import InvalidSource
from leaftracker.service_layer.unit_of_work import UnitOfWork


class FakeBatchRepository:
    def __init__(self, batches: list[Batch]):
        self._next_batch_number = 1
        self._batches = set(batches)

    def _new_reference(self) -> str:
        reference = f"batch-{self._next_batch_number:04}"
        self._next_batch_number += 1
        return reference

    def add(self, batch: Batch) -> str:
        batch.reference = self._new_reference()
        self._batches.add(batch)
        return batch.reference

    def get(self, batch_ref: str) -> Batch | None:
        matching = (batch for batch in self._batches
                    if batch.reference == batch_ref)
        return next(matching, None)


class FakeSourceRepository:
    def __init__(self, sources: list[Source]):
        self._sources = set(sources)

    def add(self, source: Source) -> str:
        self._sources.add(source)
        return source.name

    def get(self, name: str) -> Source | None:
        matching = (source for source in self._sources
                    if source.name == name)
        return next(matching, None)


class FakeSpeciesRepository:
    def __init__(self, species: list[Species]):
        self._species = set(species)

    def add(self, species: Species) -> str | None:
        self._species.add(species)
        return species.reference

    def get(self, reference: str) -> Species | None:
        matching = (species for species in self._species
                    if species.reference == reference)
        return next(matching, None)


def test_fake_reference():
    repo: BatchRepository = FakeBatchRepository([])

    references = [repo.add(Batch(Source("Habitat Links", SourceType.PROGRAM), BatchType.DELIVERY)),
                  repo.add(Batch(Source("Habitat Links", SourceType.PROGRAM), BatchType.DELIVERY)),
                  repo.add(Batch(Source("Natural Area", SourceType.NURSERY), BatchType.DELIVERY))]

    assert references == ["batch-0001", "batch-0002", "batch-0003"]


class FakeUnitOfWork:
    def __init__(self):
        self._batches: BatchRepository = FakeBatchRepository([])
        self._sources: SourceRepository = FakeSourceRepository([])
        self._species: SpeciesRepository = FakeSpeciesRepository([])
        self._commited = False

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args):
        self.rollback()

    def commit(self) -> None:
        self._commited = True

    def committed(self) -> bool:
        return self._commited

    def rollback(self) -> None:
        pass

    def batches(self) -> BatchRepository:
        return self._batches

    def sources(self) -> SourceRepository:
        return self._sources

    def species(self) -> SpeciesRepository:
        return self._species


@pytest.fixture
def uow() -> UnitOfWork:
    return FakeUnitOfWork()


def test_should_catalogue_batch(uow):
    with uow:
        batch = Batch(
            source=Source("Trillion Trees", SourceType.NURSERY),
            batch_type=BatchType.PICKUP
        )

        batch.add(Stock(species_ref="Acacia saligna", quantity=20, size=StockSize.TUBE))

        ref = uow.batches().add(batch)
        uow.commit()

        new_batch = uow.batches().get(ref)

    assert new_batch.source == Source("Trillion Trees", SourceType.NURSERY)
    assert new_batch.species() == ["Acacia saligna"]


def test_add_nursery(uow):
    services.add_nursery("Trillion Trees", uow)
    assert uow.sources().get("Trillion Trees").source_type == SourceType.NURSERY


def test_add_program(uow):
    services.add_program("Habitat Links", uow)
    assert uow.sources().get("Habitat Links").source_type == SourceType.PROGRAM


def test_add_order(uow):
    program = "Habitat Links"
    services.add_program(program, uow)
    ref = services.add_order(program, uow)

    assert ref == "batch-0001"

    assert uow.batches().get(ref).batch_type == BatchType.ORDER


def test_missing_source(uow):
    with pytest.raises(InvalidSource, match="No such source: Rodeo Nursery"):
        services.add_order("Rodeo Nursery", uow)


@pytest.fixture
def nursery(uow) -> Source:
    nursery = "Natural Area"
    services.add_nursery(nursery, uow)

    with uow:
        return uow.sources().get(nursery)


@pytest.fixture
def program(uow) -> Source:
    program = "Habitat Links"
    services.add_program(program, uow)

    with uow:
        return uow.sources().get(program)


def test_add_delivery(uow, program):
    ref = services.add_delivery(program.name, uow)
    assert uow.batches().get(ref).batch_type == BatchType.DELIVERY


def test_add_pickup(uow, nursery):
    ref = services.add_pickup(nursery.name, uow)
    assert uow.batches().get(ref).batch_type == BatchType.PICKUP


def test_add_species(uow):
    pass
