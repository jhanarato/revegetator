from collections.abc import Iterator
from typing import Self

from leaftracker.adapters.elastic_index import Document, Index
from leaftracker.adapters.elastic_repository import SpeciesRepository, SPECIES_INDEX
from leaftracker.adapters.repository import BatchRepository, SourceRepository
from leaftracker.domain.model import Species


def species_to_document(species: Species) -> Document:
    return Document(
        document_id=species.reference,
        source={
            "genus": species.names[0].genus,
            "species": species.names[0].species,
        }
    )


class ElasticUnitOfWork:
    def __init__(self, index_prefix: str = ""):
        self._species = SpeciesRepository(index_prefix + SPECIES_INDEX)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args):
        self.rollback()

    def commit(self) -> None:
        for species in self._species.added():
            document = species_to_document(species)
            species.reference = self._species.index.add_document(document)

        self._species.index.refresh()
        self._species.clear_added()

    def rollback(self) -> None:
        self._species.clear_added()

    def batches(self) -> BatchRepository:  # type: ignore
        pass

    def sources(self) -> SourceRepository:  # type: ignore
        pass

    def species(self) -> SpeciesRepository:
        return self._species
