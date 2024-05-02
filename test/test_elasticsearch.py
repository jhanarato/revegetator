from collections.abc import Generator

import pytest
from elasticsearch import Elasticsearch

from leaftracker.adapters.elastic_repository import SpeciesRepository
from leaftracker.domain.model import Species, ScientificName


@pytest.fixture
def acacia() -> ScientificName:
    return ScientificName(
        genus="Acacia",
        species="Saligna",
        is_most_recent=True
    )


@pytest.fixture
def slow_refresh() -> Generator[None]:
    es = Elasticsearch(hosts="http://localhost:9200")
    es.indices.put_settings(
        index="species",
        settings={
            "refresh_interval": "60s"
        }
    )
    yield
    es.indices.put_settings(
        index="species",
        settings={
            "refresh_interval": "1s"
        }
    )


class TestSpeciesRepository:
    def test_should_create_new_index(self):
        es = Elasticsearch(hosts="http://localhost:9200")
        es.options(ignore_status=404).indices.delete(index="species")
        repo = SpeciesRepository()
        repo.create_index()
        assert es.indices.exists(index="species")

    def test_should_delete_missing_index(self):
        es = Elasticsearch(hosts="http://localhost:9200")

        repo = SpeciesRepository()
        repo.delete_index()
        repo.delete_index()

        assert not es.indices.exists(index="species")

    def test_should_delete_existing_index(self):
        es = Elasticsearch(hosts="http://localhost:9200")

        repo = SpeciesRepository()
        repo.create_index()
        repo.delete_index()

        assert not es.indices.exists(index="species")

    def test_should_add_a_species(self, acacia):
        es = Elasticsearch(hosts="http://localhost:9200")

        repo = SpeciesRepository()
        repo.delete_index()
        repo.create_index()
        reference = repo.add(Species("acacia-saligna", acacia))

        assert es.exists(index="species", id=reference)

    def test_should_get_a_species(self, acacia, slow_refresh):
        repo = SpeciesRepository()
        repo.delete_index()
        repo.create_index()

        species_in = Species("acacia-saligna", acacia)
        repo.add(species_in)
        species_out = repo.get(species_in.reference)

        assert species_in == species_out
