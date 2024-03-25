from bookjandi.settings import KAKAO_REST_API_KEY


KAKAO_BOOK_SEARCH_URL = 'https://dapi.kakao.com/v3/search/book'
KAKAO_BOOK_SEARCH_HEADER = {
    'Authorization': f'KakaoAK {KAKAO_REST_API_KEY}'
}
KAKAO_BOOK_SEARCH_SIZE = 50
