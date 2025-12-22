from flanks.pagination import PagedResponse


class TestPagedResponse:
    def test_has_next_when_token_present(self) -> None:
        response: PagedResponse[str] = PagedResponse(
            items=["a", "b", "c"],
            next_page_token="token123",
        )
        assert response.has_next() is True

    def test_has_next_when_token_none(self) -> None:
        response: PagedResponse[str] = PagedResponse(
            items=["a", "b", "c"],
            next_page_token=None,
        )
        assert response.has_next() is False

    def test_items_accessible(self) -> None:
        response: PagedResponse[int] = PagedResponse(
            items=[1, 2, 3],
            next_page_token=None,
        )
        assert response.items == [1, 2, 3]
