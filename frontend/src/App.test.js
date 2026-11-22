import axios from 'axios';
import {BASE_URL, ROOT_SERVER, ROOT_URI} from './config/ApplicationConfig';
import {getAllCategories, getPageableCategory} from './service/CategoryService';
import {getAllCities, getCityById} from './service/CityService';
import {getClubById, getClubsByParameters, getSimilarClubsByCategoryName} from './service/ClubService';
import {getFeedbackListByClubId} from './service/FeedbackService';
import {getPageableNews} from './service/NewsService';
import {getPossibleResults, getPossibleResultsByText} from './service/SearchService';

jest.mock('axios');

const DATA = {ok: true};

beforeEach(() => {
    axios.get.mockReset();
    axios.get.mockResolvedValue({data: DATA});
});

describe('ApplicationConfig', () => {
    test('BASE_URL is ROOT_SERVER + /dev', () => {
        expect(ROOT_URI).toBe('/dev');
        expect(BASE_URL).toBe(ROOT_SERVER + '/dev');
        expect(ROOT_SERVER).toMatch(/^https?:\/\//);
    });
});

describe('CategoryService', () => {
    test('getAllCategories', async () => {
        await expect(getAllCategories()).resolves.toBe(DATA);
        expect(axios.get).toHaveBeenCalledWith(BASE_URL + '/api/categories');
    });

    test('getPageableCategory', async () => {
        await expect(getPageableCategory(2)).resolves.toBe(DATA);
        expect(axios.get).toHaveBeenCalledWith(BASE_URL + '/api/categories/search?page=2');
    });
});

describe('CityService', () => {
    test('getAllCities', async () => {
        await expect(getAllCities()).resolves.toBe(DATA);
        expect(axios.get).toHaveBeenCalledWith(BASE_URL + '/api/cities');
    });

    test('getCityById', async () => {
        await expect(getCityById(5)).resolves.toBe(DATA);
        expect(axios.get).toHaveBeenCalledWith(BASE_URL + '/api/city/5');
    });
});

describe('ClubService', () => {
    test('getClubById', async () => {
        await expect(getClubById(7)).resolves.toBe(DATA);
        expect(axios.get).toHaveBeenCalledWith(BASE_URL + '/api/club/7');
    });

    test('getSimilarClubsByCategoryName', async () => {
        await expect(getSimilarClubsByCategoryName(1, 'Sport', 'Kyiv')).resolves.toBe(DATA);
        expect(axios.get).toHaveBeenCalledWith(BASE_URL + '/api/clubs/search/similar', {
            params: {id: 1, categoryName: 'Sport', cityName: 'Kyiv'},
        });
    });

    test('getClubsByParameters', async () => {
        const params = {cityName: 'Lviv', page: 0};
        await expect(getClubsByParameters(params)).resolves.toBe(DATA);
        expect(axios.get).toHaveBeenCalledWith(BASE_URL + '/api/clubs/search', {params});
    });
});

describe('FeedbackService', () => {
    test('getFeedbackListByClubId', async () => {
        await expect(getFeedbackListByClubId(3)).resolves.toBe(DATA);
        expect(axios.get).toHaveBeenCalledWith(BASE_URL + '/api/feedbacks/3');
    });
});

describe('NewsService', () => {
    test('getPageableNews', async () => {
        await expect(getPageableNews(4)).resolves.toBe(DATA);
        expect(axios.get).toHaveBeenCalledWith(BASE_URL + '/api/newslist/search?size=4');
    });
});

describe('SearchService', () => {
    test('getPossibleResults sends empty text', async () => {
        await expect(getPossibleResults({cityName: 'Kyiv'})).resolves.toBe(DATA);
        expect(axios.get).toHaveBeenCalledWith(BASE_URL + '/api/search', {
            params: {text: '', cityName: 'Kyiv'},
        });
    });

    test('getPossibleResultsByText', async () => {
        await expect(getPossibleResultsByText('chess', {cityName: 'Kyiv'})).resolves.toBe(DATA);
        expect(axios.get).toHaveBeenCalledWith(BASE_URL + '/api/search', {
            params: {text: 'chess', cityName: 'Kyiv'},
        });
    });

    test('propagates request errors', async () => {
        axios.get.mockRejectedValueOnce(new Error('network down'));
        await expect(getPossibleResultsByText('x', {cityName: 'Kyiv'})).rejects.toThrow('network down');
    });
});
