/**
 * Combined form for creating album + pressing + collection item.
 */

import { useState, useEffect, useMemo, FormEvent, forwardRef, useImperativeHandle, useRef } from 'react';
import { albumsApi, pressingsApi, collectionApi, artistsApi, lookupApi, discogsApi } from '@/api/services';
import { Icon } from '@/components/UI';
import { mdiInformationBoxOutline, mdiLinkBoxOutline, mdiMagnify, mdiMagnifyScan } from '@mdi/js';
import {
  ArtistResponse,
  DiscogsAlbumSearchResult,
  GenreResponse,
  StyleResponse,
  CountryResponse,
  DataSource,
  VinylFormat,
  VinylSpeed,
  VinylSize,
  EditionTypeResponse,
  ReleaseTypeResponse,
  DiscogsReleaseSearchResult,
  DiscogsReleaseDetails,
} from '@/types/api';
import { usePreferences } from '@/hooks/usePreferences';
import { parseLocaleNumber } from '@/utils/format';
import './Form.css';

interface AlbumWithPressingFormProps {
  initialArtistId?: string;
  initialAlbumId?: string;
  initialAlbumTitle?: string;
  initialArtistName?: string;
  initialArtistDiscogsId?: number | null;
  initialAlbumDiscogsId?: number | null;
  onSuccess: () => void;
  onCancel: () => void;
  wizardStep?: 1 | 2 | 3;
  albumOnly?: boolean;
  albumAndPressingOnly?: boolean;
}

const VINYL_FORMATS = [VinylFormat.LP, VinylFormat.EP, VinylFormat.SINGLE, VinylFormat.MAXI, VinylFormat.CD] as const;
const VINYL_SPEEDS = [VinylSpeed.RPM_33, VinylSpeed.RPM_45, VinylSpeed.RPM_78] as const;
const VINYL_SIZES = [VinylSize.SIZE_7, VinylSize.SIZE_10, VinylSize.SIZE_12] as const;
const CD_SPEEDS = [VinylSpeed.NA] as const;
const CD_SIZES = [VinylSize.CD] as const;
type SpeedOption = typeof VINYL_SPEEDS[number] | typeof CD_SPEEDS[number];
type SizeOption = typeof VINYL_SIZES[number] | typeof CD_SIZES[number];
const FORMAT_LABELS: Record<VinylFormat, string> = {
  [VinylFormat.LP]: 'LP',
  [VinylFormat.EP]: 'EP',
  [VinylFormat.SINGLE]: 'Single',
  [VinylFormat.MAXI]: 'Maxi Single',
  [VinylFormat.CD]: 'CD',
};
const CONDITIONS = [
  { value: 'Mint', label: 'Mint (M)' },
  { value: 'NM', label: 'Near Mint (NM)' },
  { value: 'VG+', label: 'Very Good Plus (VG+)' },
  { value: 'VG', label: 'Very Good (VG)' },
  { value: 'G', label: 'Good (G)' },
  { value: 'P', label: 'Poor (P)' },
] as const;

export const AlbumWithPressingForm = forwardRef<{ submit: () => void }, AlbumWithPressingFormProps>(
  function AlbumWithPressingForm({
    initialArtistId,
    initialAlbumId,
    initialAlbumTitle,
    initialArtistName,
    initialArtistDiscogsId: _initialArtistDiscogsId,
    initialAlbumDiscogsId,
    onSuccess,
    onCancel,
    wizardStep,
    albumOnly,
    albumAndPressingOnly
  }, ref) {
  const isWizardMode = wizardStep !== undefined;
  const formRef = useRef<HTMLFormElement>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [artists, setArtists] = useState<ArtistResponse[]>([]);
  const [genres, setGenres] = useState<GenreResponse[]>([]);
  const [styles, setStyles] = useState<StyleResponse[]>([]);
  const [countries, setCountries] = useState<CountryResponse[]>([]);
  const [releaseTypes, setReleaseTypes] = useState<ReleaseTypeResponse[]>([]);
  const [editionTypes, setEditionTypes] = useState<EditionTypeResponse[]>([]);
  const [addPressing, setAddPressing] = useState(isWizardMode ? true : true);
  const [addToCollection, setAddToCollection] = useState(isWizardMode ? true : true);
  const { preferences } = usePreferences();

  const [formData, setFormData] = useState({
    // Album fields
    title: '',
    artist_id: initialArtistId || '',
    release_type: '',
    release_year: '',
    country_of_origin: '',
    genre_ids: [] as string[],
    style_ids: [] as string[],
    label: '',
    catalog_number: '',
    notes: '',
    image_url: '',
    discogs_id: null as number | null,

    // Pressing fields
    format: VinylFormat.LP as typeof VINYL_FORMATS[number],
    speed_rpm: VinylSpeed.RPM_33 as SpeedOption,
    size_inches: VinylSize.SIZE_12 as SizeOption,
    disc_count: '1',
    pressing_country: '',
    pressing_year: '',
    pressing_plant: '',
    mastering_engineer: '',
    mastering_studio: '',
    vinyl_color: '',
    label_design: '',
    pressing_image_url: '',
    edition_type: '',
    barcode: '',
    pressing_notes: '',
    discogs_release_id: null as number | null,
    discogs_master_id: null as number | null,

    // Collection fields
    media_condition: 'NM',
    sleeve_condition: 'NM',
    purchase_price: '',
    purchase_currency: 'USD',
    purchase_date: '',
    seller: '',
    location: '',
    defect_notes: '',
    collection_notes: '',
  });
  const [discogsResults, setDiscogsResults] = useState<DiscogsAlbumSearchResult[]>([]);
  const [discogsLoading, setDiscogsLoading] = useState(false);
  const [discogsError, setDiscogsError] = useState<string | null>(null);
  const [discogsSelectedId, setDiscogsSelectedId] = useState<number | null>(null);
  const [albumSearchPage, setAlbumSearchPage] = useState(1);
  const [albumSearchTotalPages, setAlbumSearchTotalPages] = useState(1);
  const [albumSearchTotal, setAlbumSearchTotal] = useState(0);
  const [pressingDiscogsResults, setPressingDiscogsResults] = useState<DiscogsReleaseSearchResult[]>([]);
  const [pressingDiscogsTotal, setPressingDiscogsTotal] = useState<number>(0);
  const [pressingDiscogsLoading, setPressingDiscogsLoading] = useState(false);
  const [pressingDiscogsError, setPressingDiscogsError] = useState<string | null>(null);
  const [pressingDiscogsSelectedId, setPressingDiscogsSelectedId] = useState<number | null>(null);
  const [importMasterReleases, setImportMasterReleases] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [isLoadingPage, setIsLoadingPage] = useState(false);
  const [openInfoBox, setOpenInfoBox] = useState<{ type: 'master' | 'pressing', id: string | number } | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<DiscogsReleaseSearchResult[]>([]);
  const [isSearchMode, setIsSearchMode] = useState(false);

  // Filter out master records (only show actual releases)
  const actualReleases = useMemo(() => {
    return pressingDiscogsResults.filter(r => r.type !== 'master');
  }, [pressingDiscogsResults]);

  // Display logic: show search results when in search mode, otherwise show paginated master releases
  const displayedReleases = useMemo(() => {
    if (isSearchMode) {
      return searchResults.filter(r => r.type !== 'master');
    }
    return actualReleases;
  }, [isSearchMode, searchResults, actualReleases]);

  const showPagination = !isSearchMode && totalPages > 1;

  // Expose submit method to parent component
  useImperativeHandle(ref, () => ({
    submit: () => {
      if (formRef.current) {
        formRef.current.requestSubmit();
      }
    }
  }));

  useEffect(() => {
    const loadData = async () => {
      try {
        const [artistsResp, genresResp, stylesResp, countriesResp, releaseTypesResp, editionTypesResp] = await Promise.all([
          artistsApi.search({ limit: 1000 }),
          lookupApi.getAllGenres(),
          lookupApi.getAllStyles(),
          lookupApi.getAllCountries(),
          lookupApi.getAllReleaseTypes(),
          lookupApi.getAllEditionTypes(),
        ]);
        // Sort artists by sort_name (or name if sort_name is not available)
        const sortedArtists = [...artistsResp.items].sort((a, b) => {
          const aName = (a.sort_name || a.name).toLowerCase();
          const bName = (b.sort_name || b.name).toLowerCase();
          return aName.localeCompare(bName);
        });
        setArtists(sortedArtists);
        setGenres(genresResp);
        setStyles(stylesResp);
        setCountries(countriesResp);
        setReleaseTypes(releaseTypesResp);
        setEditionTypes(editionTypesResp);
        if (releaseTypesResp.length > 0) {
          setFormData((prev) => ({
            ...prev,
            release_type: prev.release_type || releaseTypesResp[0].code,
          }));
        }
      } catch (err: any) {
        console.error('Failed to load lookup data:', err);
        setError('Failed to load form data. Please try again.');
      }
    };
    loadData();
  }, []);

  useEffect(() => {
    if (initialArtistId) {
      setFormData((prev) => ({
        ...prev,
        artist_id: initialArtistId,
      }));
    }
  }, [initialArtistId]);

  useEffect(() => {
    if (preferences?.currency) {
      setFormData((prev) => ({ ...prev, purchase_currency: preferences.currency }));
    }
  }, [preferences?.currency]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    if (name === 'title' || name === 'artist_id') {
      setDiscogsResults([]);
      setDiscogsError(null);
      setDiscogsSelectedId(null);
    }
    if (name === 'format') {
      setFormData((prev) => {
        if (value === VinylFormat.CD) {
          return {
            ...prev,
            format: VinylFormat.CD,
            speed_rpm: VinylSpeed.NA,
            size_inches: VinylSize.CD,
          };
        }
        const nextSpeed = prev.speed_rpm === VinylSpeed.NA ? VinylSpeed.RPM_33 : prev.speed_rpm;
        const nextSize = prev.size_inches === VinylSize.CD ? VinylSize.SIZE_12 : prev.size_inches;
        return {
          ...prev,
          format: value as VinylFormat,
          speed_rpm: nextSpeed,
          size_inches: nextSize,
        };
      });
      return;
    }
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const speedOptions = formData.format === VinylFormat.CD ? CD_SPEEDS : VINYL_SPEEDS;
  const sizeOptions = formData.format === VinylFormat.CD ? CD_SIZES : VINYL_SIZES;

  const handleMultiSelect = (e: React.ChangeEvent<HTMLSelectElement>, field: 'genre_ids' | 'style_ids') => {
    const options = e.target.selectedOptions;
    const values = Array.from(options).map(option => option.value);
    setFormData((prev) => ({ ...prev, [field]: values }));
  };

  const handleMultiSelectClick = (e: React.MouseEvent<HTMLSelectElement>, field: 'genre_ids' | 'style_ids') => {
    const clickedOption = (e.target as HTMLElement).closest('option') as HTMLOptionElement | null;

    if (clickedOption) {
      const value = clickedOption.value;
      const currentValues = formData[field];
      let newValues: string[];

      if (e.ctrlKey || e.metaKey) {
        // Ctrl/Cmd held - toggle the clicked option
        if (currentValues.includes(value)) {
          newValues = currentValues.filter(v => v !== value);
        } else {
          newValues = [...currentValues, value];
        }
      } else {
        // No Ctrl/Cmd - single select
        newValues = [value];
      }

      setFormData((prev) => ({ ...prev, [field]: newValues }));
    }
  };

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) {
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      const result = typeof reader.result === 'string' ? reader.result : '';
      setFormData((prev) => ({
        ...prev,
        image_url: result,
      }));
    };
    reader.readAsDataURL(file);
  };

  const handleImageRemove = () => {
    setFormData((prev) => ({
      ...prev,
      image_url: '',
    }));
  };

  const resolveCountryCode = (value: string | undefined | null) => {
    if (!value) return '';
    const trimmed = value.trim();
    if (trimmed.length === 2) {
      const code = trimmed.toUpperCase();
      return countries.some((country) => country.code === code) ? code : '';
    }
    const match = countries.find(
      (country) => country.name.toLowerCase() === trimmed.toLowerCase()
    );
    return match?.code || '';
  };

  const resolveGenreIds = async (names: string[] | undefined) => {
    const result: string[] = [];
    for (const name of names ?? []) {
      const trimmed = name.trim();
      if (!trimmed) continue;
      const existing = genres.find((genre) => genre.name.toLowerCase() === trimmed.toLowerCase());
      if (existing) {
        result.push(existing.id);
        continue;
      }
      try {
        const created = await lookupApi.createGenre({ name: trimmed });
        setGenres((prev) => [...prev, created]);
        result.push(created.id);
      } catch (err) {
        console.warn('Failed to create genre from Discogs:', err);
      }
    }
    return result;
  };

  const resolveStyleIds = async (names: string[] | undefined) => {
    const result: string[] = [];
    for (const name of names ?? []) {
      const trimmed = name.trim();
      if (!trimmed) continue;
      const existing = styles.find((style) => style.name.toLowerCase() === trimmed.toLowerCase());
      if (existing) {
        result.push(existing.id);
        continue;
      }
      try {
        const created = await lookupApi.createStyle({ name: trimmed });
        setStyles((prev) => [...prev, created]);
        result.push(created.id);
      } catch (err) {
        console.warn('Failed to create style from Discogs:', err);
      }
    }
    return result;
  };

  const resolveReleaseType = async (value: string | undefined | null) => {
    if (!value) return null;
    const trimmed = value.trim();
    if (!trimmed) return null;
    const existing = releaseTypes.find(
      (type) =>
        type.code.toLowerCase() === trimmed.toLowerCase() ||
        type.name.toLowerCase() === trimmed.toLowerCase()
    );
    if (existing) {
      return existing.code;
    }
    try {
      const created = await lookupApi.createReleaseType({ code: trimmed, name: trimmed });
      setReleaseTypes((prev) => [...prev, created]);
      return created.code;
    } catch (err) {
      console.warn('Failed to create release type from Discogs:', err);
      return null;
    }
  };

  const getSelectedArtistDiscogsId = () => {
    const selected = artists.find((artist) => artist.id === formData.artist_id);
    return selected?.discogs_id ?? null;
  };

  const handleDiscogsSearch = async (page: number = 1) => {
    const query = formData.title.trim();
    const artistDiscogsId = getSelectedArtistDiscogsId();
    if (!artistDiscogsId || query.length < 3) return;

    if (page === 1) {
      setDiscogsLoading(true);
    }
    setDiscogsError(null);

    try {
      const response = await discogsApi.searchAlbums(artistDiscogsId, query, 10, page);
      setDiscogsResults(response.items);
      setAlbumSearchTotal(response.total || response.items.length);
      setAlbumSearchPage(response.page || page);
      setAlbumSearchTotalPages(response.pages || Math.ceil((response.total || response.items.length) / 10));
    } catch (err: any) {
      setDiscogsError(err.response?.data?.detail || 'Failed to search Discogs');
    } finally {
      setDiscogsLoading(false);
    }
  };

  const handleDiscogsSelect = async (albumId: number, albumType?: string) => {
    setDiscogsSelectedId(albumId);
    setDiscogsLoading(true);
    setDiscogsError(null);
    try {
      const details = await discogsApi.getAlbum(albumId, albumType);
      const countryCode = resolveCountryCode(details.country);
      const genreIds = await resolveGenreIds(details.genres);
      const styleIds = await resolveStyleIds(details.styles);
      const resolvedReleaseType = await resolveReleaseType(details.type);
      setFormData((prev) => ({
        ...prev,
        title: details.title || prev.title,
        release_year: details.year ? String(details.year) : prev.release_year,
        country_of_origin: countryCode || prev.country_of_origin,
        label: details.label || prev.label,
        catalog_number: details.catalog_number || prev.catalog_number,
        image_url: details.image_url || prev.image_url,
        discogs_id: details.id || prev.discogs_id,
        genre_ids: genreIds.length ? genreIds : prev.genre_ids,
        style_ids: styleIds.length ? styleIds : prev.style_ids,
        release_type: resolvedReleaseType || prev.release_type,
        discogs_release_id: null,
        discogs_master_id: null,
      }));
      resetPressingDiscogsState();
      setDiscogsResults([]);
    } catch (err: any) {
      setDiscogsError(err.response?.data?.detail || 'Failed to load Discogs album');
    } finally {
      setDiscogsLoading(false);
    }
  };

  const handlePressingImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) {
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      const result = typeof reader.result === 'string' ? reader.result : '';
      setFormData((prev) => ({
        ...prev,
        pressing_image_url: result,
      }));
    };
    reader.readAsDataURL(file);
  };

  const handlePressingImageRemove = () => {
    setFormData((prev) => ({
      ...prev,
      pressing_image_url: '',
    }));
  };

  const mapDiscogsFormat = (details: DiscogsReleaseDetails) => {
    const tokens = [
      ...(details.formats || []),
      ...(details.format_descriptions || []),
    ].map((value) => value.toLowerCase());
    const combined = tokens.join(' ');

    if (combined.includes('cd')) return VinylFormat.CD;
    if (combined.includes('ep')) return VinylFormat.EP;
    if (combined.includes('single')) return VinylFormat.SINGLE;
    if (combined.includes('maxi')) return VinylFormat.MAXI;
    return VinylFormat.LP;
  };

  const mapDiscogsSpeed = (details: DiscogsReleaseDetails) => {
    const tokens = [
      ...(details.formats || []),
      ...(details.format_descriptions || []),
    ].map((value) => value.toLowerCase());
    const combined = tokens.join(' ');

    if (combined.includes('cd')) return VinylSpeed.NA;
    if (combined.includes('78')) return VinylSpeed.RPM_78;
    if (combined.includes('45')) return VinylSpeed.RPM_45;
    return VinylSpeed.RPM_33;
  };

  const mapDiscogsSize = (details: DiscogsReleaseDetails) => {
    const tokens = [
      ...(details.formats || []),
      ...(details.format_descriptions || []),
    ].map((value) => value.toLowerCase());
    const combined = tokens.join(' ');

    if (combined.includes('cd')) return VinylSize.CD;
    if (combined.includes('7\"')) return VinylSize.SIZE_7;
    if (combined.includes('10\"')) return VinylSize.SIZE_10;
    return VinylSize.SIZE_12;
  };

  const resolveEditionType = async (value: string | undefined | null) => {
    if (!value) return null;
    const trimmed = value.trim();
    if (!trimmed) return null;
    const existing = editionTypes.find(
      (type) =>
        type.code.toLowerCase() === trimmed.toLowerCase() ||
        type.name.toLowerCase() === trimmed.toLowerCase()
    );
    if (existing) {
      return existing.code;
    }
    try {
      const created = await lookupApi.createEditionType({ code: trimmed, name: trimmed });
      setEditionTypes((prev) => [...prev, created]);
      return created.code;
    } catch (err) {
      console.warn('Failed to create edition type from Discogs:', err);
      return null;
    }
  };

  const extractEditionTypeFromFormat = (value?: string | null) => {
    if (!value) return null;
    const tokens = value
      .split(/[·,]/)
      .map((token) => token.trim())
      .filter(Boolean);
    for (const token of tokens) {
      const existing = editionTypes.find(
        (type) =>
          type.code.toLowerCase() === token.toLowerCase() ||
          type.name.toLowerCase() === token.toLowerCase()
      );
      if (existing) {
        return existing.code;
      }
    }
    for (let i = tokens.length - 1; i >= 0; i -= 1) {
      const token = tokens[i];
      if (token.toLowerCase().includes('edition')) {
        return token;
      }
    }
    for (let i = tokens.length - 1; i >= 0; i -= 1) {
      const token = tokens[i];
      if (token.toLowerCase().includes('promo')) {
        return 'Promo';
      }
    }
    for (const token of tokens) {
      const lowered = token.toLowerCase();
      if (lowered.includes('limited')) return 'Limited';
      if (lowered.includes('numbered')) return 'Numbered';
      if (lowered.includes('reissue')) return 'Reissue';
      if (lowered.includes('remaster')) return 'Remaster';
    }
    return null;
  };

  const applyDiscogsRelease = async (details: DiscogsReleaseDetails, fallbackEditionType?: string | null) => {
    const identifiers = details.identifiers || details.barcode || '';
    const requestedEditionType = (details.edition_type && details.edition_type !== 'Standard')
      ? details.edition_type
      : (fallbackEditionType || details.edition_type || 'Standard');
    const resolvedEditionType = await resolveEditionType(requestedEditionType);
    const vinylColor = details.vinyl_color || 'Black';
    setFormData((prev) => ({
      ...prev,
      format: mapDiscogsFormat(details),
      speed_rpm: mapDiscogsSpeed(details),
      size_inches: mapDiscogsSize(details),
      disc_count: details.disc_count ? String(details.disc_count) : prev.disc_count,
      pressing_year: details.year ? String(details.year) : prev.pressing_year,
      pressing_country: resolveCountryCode(details.country) || prev.pressing_country,
      pressing_plant: details.pressing_plant || prev.pressing_plant,
      mastering_engineer: details.mastering_engineer || prev.mastering_engineer,
      mastering_studio: details.mastering_studio || prev.mastering_studio,
      vinyl_color: vinylColor || prev.vinyl_color,
      label_design: details.label || prev.label_design,
      edition_type: resolvedEditionType || prev.edition_type,
      barcode: identifiers || prev.barcode,
      pressing_image_url: details.image_url || prev.pressing_image_url,
      pressing_notes: prev.pressing_notes,
      discogs_release_id: details.id,
      discogs_master_id: details.master_id || prev.discogs_master_id,
    }));
  };

  const resetPressingDiscogsState = () => {
    setPressingDiscogsResults([]);
    setPressingDiscogsError(null);
    setPressingDiscogsSelectedId(null);
    setImportMasterReleases(false);
    setSearchQuery('');
    setSearchResults([]);
    setIsSearchMode(false);
  };

  const closePressingDiscogsResults = () => {
    setPressingDiscogsResults([]);
    setPressingDiscogsError(null);
    setPressingDiscogsSelectedId(null);
  };

  const handlePressingDiscogsSearch = async (page: number = 1) => {
    const discogsId = initialAlbumDiscogsId || formData.discogs_id;
    if (!discogsId) {
      setPressingDiscogsError('Select a Discogs album to search pressings.');
      return;
    }

    const isSearch = searchQuery.trim().length >= 4;

    setIsLoadingPage(true);
    if (page === 1) {
      setPressingDiscogsLoading(true);
    }
    setPressingDiscogsError(null);
    setPressingDiscogsSelectedId(null);
    setImportMasterReleases(false);

    try {
      if (isSearch) {
        // Perform search
        const response = await discogsApi.searchMasterReleases(
          discogsId,
          searchQuery.trim(),
          10
        );
        setSearchResults(response.items);
        setIsSearchMode(true);
        setPressingDiscogsTotal(response.total || response.items.length);
        setCurrentPage(1);
        setTotalPages(1);

        if (response.items.length === 0) {
          setPressingDiscogsError('No pressings found for this search.');
        }
      } else {
        // Fetch paginated master releases list
        const response = await discogsApi.getMasterReleases(discogsId, page, 10);
        console.log('Discogs API Response:', response);
        console.log('Total from API:', response.total);
        console.log('Items count:', response.items.length);
        setPressingDiscogsResults(response.items);
        setIsSearchMode(false);
        setPressingDiscogsTotal(response.total || response.items.length);
        setCurrentPage(response.page || page);
        setTotalPages(response.pages || 1);

        console.log('Set total to:', response.total || response.items.length);
        if (response.items.length === 0) {
          setPressingDiscogsError('No pressings found for this master.');
        }

      }
    } catch (err: any) {
      // Check for rate limit error (429)
      if (err.response?.status === 429) {
        setPressingDiscogsError('⚠️ Discogs API rate limit exceeded. Please wait a moment and try again.');
      } else {
        setPressingDiscogsError(err.response?.data?.detail || err.message || 'Discogs lookup failed.');
      }
    } finally {
      setPressingDiscogsLoading(false);
      setIsLoadingPage(false);
    }
  };

  const handlePressingDiscogsSelect = async (result: DiscogsReleaseSearchResult) => {
    setPressingDiscogsSelectedId(result.id);
    setImportMasterReleases(false);
    if (result.type === 'master') {
      setFormData((prev) => ({
        ...prev,
        discogs_master_id: result.id,
        discogs_release_id: null,
      }));
      closePressingDiscogsResults();
      return;
    }

    try {
      setPressingDiscogsLoading(true);
      const details = await discogsApi.getRelease(result.id);
      const fallbackEditionType = extractEditionTypeFromFormat(result.format);
      await applyDiscogsRelease(details, fallbackEditionType);
      resetPressingDiscogsState();
    } catch (err: any) {
      setPressingDiscogsError(err.response?.data?.detail || err.message || 'Discogs release lookup failed.');
    } finally {
      setPressingDiscogsLoading(false);
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    // Skip album validation if we already have an album ID
    if (!initialAlbumId) {
      if (!formData.title.trim()) {
        setError('Title is required');
        return;
      }
      if (!formData.artist_id) {
        setError('Artist is required');
        return;
      }
    }

    const discCount = parseInt(formData.disc_count);
    if (addPressing && (isNaN(discCount) || discCount < 1 || discCount > 10)) {
      setError('Disc count must be between 1 and 10');
      return;
    }

    setLoading(true);

    try {
      // Step 1: Create album (or use existing album ID)
      let albumId: string;

      if (initialAlbumId) {
        // Use the provided album ID (we're adding a pressing to an existing album)
        albumId = initialAlbumId;
      } else {
        // Create a new album
        const albumPayload: any = {
          title: formData.title,
          artist_id: formData.artist_id,
          release_type: formData.release_type,
          genre_ids: formData.genre_ids,
          style_ids: formData.style_ids,
          data_source: DataSource.USER,
        };

        if (formData.release_year) {
          const year = parseInt(formData.release_year);
          if (!isNaN(year)) albumPayload.release_year = year;
        }
        if (formData.country_of_origin) albumPayload.country_of_origin = formData.country_of_origin;
        if (formData.label) albumPayload.label = formData.label;
        if (formData.catalog_number) albumPayload.catalog_number = formData.catalog_number;
        if (formData.notes) albumPayload.notes = formData.notes;
        if (formData.image_url) albumPayload.image_url = formData.image_url;
        if (formData.discogs_id) albumPayload.discogs_id = formData.discogs_id;

        const album = await albumsApi.create(albumPayload);
        albumId = album.id;
      }

      // Skip pressing and collection if albumOnly is true
      if (!albumOnly && addPressing) {
        // Step 2: Create pressing
        const pressingPayload: any = {
          album_id: albumId,
          format: formData.format,
          speed_rpm: formData.speed_rpm,
          size_inches: formData.size_inches,
          disc_count: discCount,
        };

        if (formData.pressing_country) pressingPayload.country = formData.pressing_country;
        if (formData.pressing_year) {
          const year = parseInt(formData.pressing_year);
          if (!isNaN(year)) pressingPayload.release_year = year;
        }
        if (formData.pressing_plant) pressingPayload.pressing_plant = formData.pressing_plant;
        if (formData.mastering_engineer) pressingPayload.mastering_engineer = formData.mastering_engineer;
        if (formData.mastering_studio) pressingPayload.mastering_studio = formData.mastering_studio;
        if (formData.vinyl_color) pressingPayload.vinyl_color = formData.vinyl_color;
        if (formData.label_design) pressingPayload.label_design = formData.label_design;
        if (formData.pressing_image_url) pressingPayload.image_url = formData.pressing_image_url;
        if (formData.edition_type) pressingPayload.edition_type = formData.edition_type;
        if (formData.barcode) pressingPayload.barcode = formData.barcode;
        if (formData.pressing_notes) pressingPayload.notes = formData.pressing_notes;
        if (formData.discogs_release_id) pressingPayload.discogs_release_id = formData.discogs_release_id;
        if (formData.discogs_master_id) pressingPayload.discogs_master_id = formData.discogs_master_id;
        if (importMasterReleases) pressingPayload.import_master_releases = true;

        const pressing = await pressingsApi.create(pressingPayload);

        // Step 3: Optionally add to collection (skip if albumAndPressingOnly)
        if (!albumAndPressingOnly && addToCollection) {
          const collectionPayload: any = {
            pressing_id: pressing.id,
            media_condition: formData.media_condition,
            sleeve_condition: formData.sleeve_condition,
          };

          if (formData.purchase_price) {
            const price = parseLocaleNumber(formData.purchase_price);
            if (price !== null) collectionPayload.purchase_price = price;
          }
          if (formData.purchase_currency) collectionPayload.purchase_currency = formData.purchase_currency;
          if (formData.purchase_date) collectionPayload.purchase_date = formData.purchase_date;
          if (formData.seller) collectionPayload.seller = formData.seller;
          if (formData.location) collectionPayload.location = formData.location;
          if (formData.defect_notes) collectionPayload.defect_notes = formData.defect_notes;
          if (formData.collection_notes) collectionPayload.notes = formData.collection_notes;

          await collectionApi.addItem(collectionPayload);
        }
      }

      onSuccess();
    } catch (err: any) {
      console.error('Failed to create album:', err);
      console.error('Error response:', err.response?.data);
      const detail = err.response?.data?.detail;
      if (Array.isArray(detail)) {
        // Pydantic validation errors
        const errors = detail.map((e: any) => `${e.loc?.join('.')}: ${e.msg}`).join('; ');
        setError(`Validation errors: ${errors}`);
      } else {
        setError(detail || err.message || 'Failed to create album');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <form ref={formRef} className="form" onSubmit={handleSubmit}>
      {error && <div className="form-error">{error}</div>}

      {(!isWizardMode || wizardStep === 1) && (
        <>
          <h3>Album Information</h3>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="artist_id">
                Artist <span className="required">*</span>
              </label>
              <select
                id="artist_id"
                name="artist_id"
                value={formData.artist_id}
                onChange={handleChange}
                required
              >
                <option value="">Select an artist...</option>
                {artists.map((artist) => (
                  <option key={artist.id} value={artist.id}>
                    {artist.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group" style={{ gridColumn: 'span 2' }}>
              <label htmlFor="title">
                Title <span className="required">*</span>
              </label>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <input
                  type="text"
                  id="title"
                  name="title"
                  value={formData.title}
                  onChange={handleChange}
                  placeholder="Abbey Road"
                  required
                  maxLength={500}
                  style={{ flex: 1 }}
                />
                <button
                  type="button"
                  className="btn-primary"
                  onClick={() => handleDiscogsSearch()}
                  disabled={!getSelectedArtistDiscogsId() || formData.title.trim().length < 3 || discogsLoading}
                  title="Search Discogs"
                  style={{
                    minWidth: '40px',
                    height: '40px',
                    padding: '0.5rem',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}
                >
                  <span style={{ width: '20px', height: '20px', display: 'flex', color: 'white' }}>
                    <Icon path={mdiMagnify} />
                  </span>
                </button>
              </div>
            </div>
          </div>

          {discogsError && (
            <div className="form-group">
              <div className="form-hint-error">{discogsError}</div>
            </div>
          )}

          {discogsLoading && (
            <div style={{ display: 'flex', justifyContent: 'center', padding: '2rem' }}>
              <div style={{
                border: '4px solid #2d6a6a',
                borderTop: '4px solid #4d9a9a',
                borderRadius: '50%',
                width: '40px',
                height: '40px',
                animation: 'spin 1s linear infinite'
              }} />
              <style>{`
                @keyframes spin {
                  0% { transform: rotate(0deg); }
                  100% { transform: rotate(360deg); }
                }
              `}</style>
            </div>
          )}

          {discogsResults.length > 0 && (
          <div className="discogs-results" style={{ width: '65%', margin: '0 auto' }}>
            <div className="discogs-results-header">
              Select Album ({albumSearchTotal} result{albumSearchTotal !== 1 ? 's' : ''})
            </div>
            <div className="discogs-results-list">
              {discogsResults.map((result) => (
                <button
                  key={`${result.id}-${result.type ?? 'master'}`}
                  type="button"
                  className={`discogs-result ${discogsSelectedId === result.id ? 'is-selected' : ''}`}
                  onClick={() => handleDiscogsSelect(result.id, result.type)}
                  disabled={discogsLoading}
                >
                  <div className="discogs-result-thumb">
                    {result.thumb_url ? (
                      <img src={result.thumb_url} alt={result.title} />
                    ) : (
                      <span className="discogs-result-placeholder">?</span>
                    )}
                  </div>
                  <div className="discogs-result-content">
                    <div className="discogs-result-name">{result.title}</div>
                    <div className="discogs-result-meta">
                      {result.year ? result.year : 'Unknown year'}
                    </div>
                  </div>
                </button>
              ))}
            </div>
            {albumSearchTotalPages > 1 && (
              <div className="pagination" style={{ marginTop: '1rem', padding: '0 1rem' }}>
                <div className="pagination-controls">
                  <button
                    type="button"
                    onClick={() => handleDiscogsSearch(albumSearchPage - 1)}
                    disabled={albumSearchPage === 1 || discogsLoading}
                    className="pagination-button"
                  >
                    Previous
                  </button>
                  <div className="pagination-info">
                    Page {albumSearchPage} of {albumSearchTotalPages}
                  </div>
                  <button
                    type="button"
                    onClick={() => handleDiscogsSearch(albumSearchPage + 1)}
                    disabled={albumSearchPage === albumSearchTotalPages || discogsLoading}
                    className="pagination-button"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
            <div className="discogs-results-footer">
              <button
                type="button"
                className="discogs-results-cancel"
                onClick={() => {
                  setDiscogsResults([]);
                  setDiscogsSelectedId(null);
                  setAlbumSearchPage(1);
                  setAlbumSearchTotalPages(1);
                  setAlbumSearchTotal(0);
                }}
              >
                Cancel
              </button>
            </div>
          </div>
          )}

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="country_of_origin">Country</label>
              <select
                id="country_of_origin"
                name="country_of_origin"
                value={formData.country_of_origin}
                onChange={handleChange}
              >
                <option value="">Select...</option>
                {countries.map((country) => (
                  <option key={country.code} value={country.code}>
                    {country.name} ({country.code})
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="release_year">Year</label>
              <input
                type="number"
                id="release_year"
                name="release_year"
                value={formData.release_year}
                onChange={handleChange}
                placeholder="1969"
                min="1900"
                max="2100"
              />
            </div>

            <div className="form-group">
              <label htmlFor="release_type">Type</label>
              <select
                id="release_type"
                name="release_type"
                value={formData.release_type}
                onChange={handleChange}
              >
                <option value="">Select...</option>
                {releaseTypes.map((type) => (
                  <option key={type.code} value={type.code}>
                    {type.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="label">Label</label>
              <input
                type="text"
                id="label"
                name="label"
                value={formData.label}
                onChange={handleChange}
                placeholder="Apple Records"
                maxLength={200}
              />
            </div>

            <div className="form-group">
              <label htmlFor="catalog_number">Catalog Number</label>
              <input
                type="text"
                id="catalog_number"
                name="catalog_number"
                value={formData.catalog_number}
                onChange={handleChange}
                placeholder="PCS 7088"
                maxLength={100}
              />
            </div>

            <div className="form-group">
              <label htmlFor="discogs_id">Discogs ID</label>
              <input
                type="text"
                id="discogs_id"
                name="discogs_id"
                value={formData.discogs_id ?? ''}
                disabled
                placeholder="Select album"
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="genre_ids">Genres</label>
              <select
                id="genre_ids"
                name="genre_ids"
                multiple
                size={5}
                value={formData.genre_ids}
                onChange={(e) => handleMultiSelect(e, 'genre_ids')}
                onClick={(e) => handleMultiSelectClick(e, 'genre_ids')}
              >
                {genres.map((genre) => (
                  <option key={genre.id} value={genre.id}>
                    {genre.name}
                  </option>
                ))}
              </select>
              <small>Click to select. Hold Ctrl/Cmd for multiple</small>
            </div>

            <div className="form-group">
              <label htmlFor="style_ids">Styles</label>
              <select
                id="style_ids"
                name="style_ids"
                multiple
                size={5}
                value={formData.style_ids}
                onChange={(e) => handleMultiSelect(e, 'style_ids')}
                onClick={(e) => handleMultiSelectClick(e, 'style_ids')}
              >
                {styles.map((style) => (
                  <option key={style.id} value={style.id}>
                    {style.name}
                  </option>
                ))}
              </select>
              <small>Click to select. Hold Ctrl/Cmd for multiple</small>
            </div>
          </div>

          <div className="form-group" style={{ marginRight: '20px' }}>
            <label htmlFor="notes">Album Notes</label>
            <textarea
              id="notes"
              name="notes"
              value={formData.notes}
              onChange={handleChange}
              placeholder="Original UK release"
              rows={2}
            />
          </div>

      <div className="form-group">
        <label htmlFor="image_upload">Album Image</label>
        <div className="image-upload">
          <div className="image-preview" aria-live="polite">
            {formData.image_url ? (
              <img src={formData.image_url} alt={`${formData.title || 'Album'} preview`} />
            ) : (
              <span>No image selected</span>
            )}
          </div>
          <div className="image-actions">
            <input
              type="file"
              id="image_upload"
              name="image_upload"
              accept="image/*"
              onChange={handleImageChange}
            />
            {formData.image_url && (
              <button
                type="button"
                className="btn-secondary btn-image-remove"
                onClick={handleImageRemove}
                disabled={loading}
              >
                Remove Image
              </button>
            )}
          </div>
        </div>
        <small>PNG or JPG recommended. Smaller images load faster.</small>
          </div>
        </>
      )}

      {!isWizardMode && (
        <div className="form-group" style={{ marginTop: '1.5rem', borderTop: '1px solid var(--color-border-strong)', paddingTop: '1.5rem' }}>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={addPressing}
              onChange={(e) => {
                const checked = e.target.checked;
                setAddPressing(checked);
                if (!checked) {
                  setAddToCollection(false);
                  resetPressingDiscogsState();
                }
              }}
            />
            <span>Add a pressing</span>
          </label>
        </div>
      )}

      {addPressing && (!isWizardMode || wizardStep === 2) && (
        <>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1rem', marginRight: '20px' }}>
            <h3 style={{ margin: 0 }}>Pressing Details</h3>
            <div style={{ display: 'flex', gap: '0.5rem', width: '50%', justifyContent: 'flex-end' }}>
              <input
                type="text"
                placeholder="Search by barcode, catalog #, label..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => {
                  const discogsIdAvailable = initialAlbumDiscogsId || formData.discogs_id;
                  if (e.key === 'Enter' && discogsIdAvailable && !pressingDiscogsLoading) {
                    e.preventDefault();
                    handlePressingDiscogsSearch();
                  }
                }}
                disabled={!initialAlbumDiscogsId && !formData.discogs_id}
                style={{
                  flex: 1,
                  padding: '0.5rem',
                  borderRadius: '4px',
                  border: '1px solid #2d6a6a',
                  background: '#1d4a4a',
                  color: '#e0e0e0'
                }}
              />
              <button
                type="button"
                className="btn-primary"
                onClick={() => handlePressingDiscogsSearch()}
                disabled={(!initialAlbumDiscogsId && !formData.discogs_id) || pressingDiscogsLoading}
                title={searchQuery.trim().length >= 4 ? 'Search Discogs' : 'Browse Discogs'}
                style={{
                  minWidth: '40px',
                  height: '40px',
                  padding: '0.5rem',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              >
                <span style={{ width: '20px', height: '20px', display: 'flex', color: 'white' }}>
                  <Icon path={searchQuery.trim().length >= 4 ? mdiMagnifyScan : mdiMagnify} />
                </span>
              </button>
            </div>
          </div>

          {/* Show Artist and Album Title when in Pressing Wizard mode */}
          {initialAlbumId && initialAlbumTitle && initialArtistName && (
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="artist_name_readonly">Artist</label>
                <input
                  type="text"
                  id="artist_name_readonly"
                  value={initialArtistName}
                  disabled
                  style={{ background: 'var(--color-background-subtle)', color: 'var(--color-text-muted)', cursor: 'not-allowed' }}
                />
              </div>
              <div className="form-group" style={{ gridColumn: 'span 2' }}>
                <label htmlFor="album_title_readonly">Album Title</label>
                <input
                  type="text"
                  id="album_title_readonly"
                  value={initialAlbumTitle}
                  disabled
                  style={{ background: 'var(--color-background-subtle)', color: 'var(--color-text-muted)', cursor: 'not-allowed' }}
                />
              </div>
            </div>
          )}

          {!initialAlbumDiscogsId && !formData.discogs_id && (
            <small>Select a Discogs album to enable pressing lookup.</small>
          )}

          {pressingDiscogsError && <div className="form-hint-error">{pressingDiscogsError}</div>}

          {pressingDiscogsLoading && (
            <div style={{ display: 'flex', justifyContent: 'center', padding: '2rem' }}>
              <div style={{
                border: '4px solid #2d6a6a',
                borderTop: '4px solid #4d9a9a',
                borderRadius: '50%',
                width: '40px',
                height: '40px',
                animation: 'spin 1s linear infinite'
              }} />
            </div>
          )}

          {displayedReleases.length > 0 && (
            <div className="discogs-results" style={{ width: '90%', margin: '0 auto' }}>
              <div className="discogs-results-header">
                {isSearchMode ? (
                  <span>Search Results ({searchResults.length})</span>
                ) : (
                  <span>Select Pressing ({pressingDiscogsTotal} release{pressingDiscogsTotal !== 1 ? 's' : ''})</span>
                )}
              </div>
              <div className="discogs-results-list">
                {displayedReleases.map((result) => {
                  const isSelected = pressingDiscogsSelectedId === result.id;
                  const isInfoOpen = openInfoBox?.type === 'pressing' && openInfoBox?.id === result.id;

                  return (
                    <div key={`${result.type}-${result.id}`} style={{ position: 'relative', display: 'flex', gap: '0.5rem', alignItems: 'flex-start' }}>
                      <button
                        type="button"
                        className={`discogs-result ${isSelected ? 'is-selected' : ''}`}
                        disabled={pressingDiscogsLoading || isLoadingPage}
                        onClick={() => handlePressingDiscogsSelect(result)}
                        style={{ flex: 1 }}
                      >
                        <div className="discogs-result-thumb">
                          {result.thumb_url ? (
                            <img src={result.thumb_url} alt={`${result.title} artwork`} />
                          ) : (
                            <span className="discogs-result-placeholder">?</span>
                          )}
                        </div>
                        <div className="discogs-result-content">
                          <div className="discogs-result-name">
                            {result.title}
                            <span className="discogs-result-tag">RELEASE</span>
                          </div>
                          <div className="discogs-result-meta">
                            {[result.year, result.country, result.label, result.format].filter(Boolean).join(' · ')}
                          </div>
                        </div>
                      </button>
                      <button
                        type="button"
                        className="info-icon-btn"
                        onClick={(e) => {
                          e.stopPropagation();
                          setOpenInfoBox(isInfoOpen ? null : { type: 'pressing', id: result.id });
                        }}
                        style={{
                          padding: '4px',
                          background: 'none',
                          border: 'none',
                          cursor: 'pointer',
                          color: '#b9c9ff',
                          flexShrink: 0
                        }}
                        title="View release details"
                      >
                        <Icon path={mdiInformationBoxOutline} size={18} />
                      </button>
                      <a
                        href={`https://www.discogs.com/release/${result.id}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{
                          padding: '4px',
                          color: '#b9c9ff',
                          display: 'flex',
                          alignItems: 'center',
                          flexShrink: 0
                        }}
                        title="Open in Discogs"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <Icon path={mdiLinkBoxOutline} size={18} />
                      </a>
                      {isInfoOpen && (
                        <div className="info-box" style={{
                          padding: '0.75rem',
                          background: '#1d4a4a',
                          border: '1px solid #2d6a6a',
                          borderRadius: '4px',
                          marginTop: '0.5rem',
                          fontSize: '0.85rem',
                          color: '#e0e0e0'
                        }}>
                          <div style={{ marginBottom: '0.5rem' }}>
                            <strong>Discogs Release ID:</strong> {result.id}
                          </div>
                          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                            <div><strong>Year:</strong> {result.year || 'Unknown'}</div>
                            <div><strong>Label:</strong> {result.label || 'Unknown'}</div>
                            <div><strong>Media Type:</strong> {result.format || 'Unknown'}</div>
                            <div><strong>Country:</strong> {result.country || 'Unknown'}</div>
                            <div><strong>Catalog:</strong> {result.catalog_number || 'N/A'}</div>
                          </div>
                          <div style={{ marginTop: '0.5rem' }}>
                            <div><strong>Barcode and Other Identifiers:</strong></div>
                            <div style={{
                              marginTop: '0.25rem',
                              paddingLeft: '1rem',
                              whiteSpace: 'pre-wrap',
                              fontSize: '0.85rem',
                              maxHeight: '200px',
                              overflowY: 'auto'
                            }}>
                              {result.identifiers || (result.barcode ? `Barcode: ${result.barcode}` : 'None')}
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
              {showPagination && (
                <div className="pagination" style={{ marginTop: '1rem', padding: '0 1rem' }}>
                  <div className="pagination-controls">
                    <button
                      type="button"
                      onClick={() => handlePressingDiscogsSearch(currentPage - 1)}
                      disabled={currentPage === 1 || isLoadingPage}
                      className="pagination-button"
                    >
                      Previous
                    </button>
                    <div className="pagination-info">
                      Page {currentPage} of {totalPages} ({pressingDiscogsTotal} total)
                    </div>
                    <button
                      type="button"
                      onClick={() => handlePressingDiscogsSearch(currentPage + 1)}
                      disabled={currentPage === totalPages || isLoadingPage}
                      className="pagination-button"
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}
              <div className="discogs-results-footer">
                <button type="button" className="discogs-results-cancel" onClick={resetPressingDiscogsState}>
                  Clear results
                </button>
              </div>
            </div>
          )}

          {formData.discogs_master_id && !formData.discogs_release_id && (
            <div className="form-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={importMasterReleases}
                  onChange={(e) => setImportMasterReleases(e.target.checked)}
                />
                <span>Create all pressings under this master (queued)</span>
              </label>
              <small>Child releases will be created in the background.</small>
            </div>
          )}

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="format">
                Format <span className="required">*</span>
              </label>
              <select
                id="format"
                name="format"
                value={formData.format}
                onChange={handleChange}
                required
              >
                {VINYL_FORMATS.map((format) => (
                  <option key={format} value={format}>
                    {FORMAT_LABELS[format]}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="speed_rpm">Speed</label>
              <select
                id="speed_rpm"
                name="speed_rpm"
                value={formData.speed_rpm}
                onChange={handleChange}
              >
                {speedOptions.map((speed) => (
                  <option key={speed} value={speed}>
                    {speed === VinylSpeed.NA ? 'N/A' : `${speed} RPM`}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="size_inches">Size</label>
              <select
                id="size_inches"
                name="size_inches"
                value={formData.size_inches}
                onChange={handleChange}
              >
                {sizeOptions.map((size) => (
                  <option key={size} value={size}>
                    {size}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="disc_count">Disc Count</label>
              <input
                type="number"
                id="disc_count"
                name="disc_count"
                value={formData.disc_count}
                onChange={handleChange}
                min="1"
                max="10"
              />
            </div>

            <div className="form-group">
              <label htmlFor="pressing_country">Pressing Country</label>
              <select
                id="pressing_country"
                name="pressing_country"
                value={formData.pressing_country}
                onChange={handleChange}
              >
                <option value="">Select country...</option>
                {countries.map((country) => (
                  <option key={country.code} value={country.code}>
                    {country.name} ({country.code})
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="pressing_year">Pressing Year</label>
              <input
                type="number"
                id="pressing_year"
                name="pressing_year"
                value={formData.pressing_year}
                onChange={handleChange}
                placeholder="1969"
                min="1900"
                max="2100"
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="vinyl_color">Vinyl Color</label>
              <input
                type="text"
                id="vinyl_color"
                name="vinyl_color"
                value={formData.vinyl_color}
                onChange={handleChange}
                placeholder="Black"
                maxLength={100}
              />
            </div>

            <div className="form-group">
              <label htmlFor="edition_type">Edition Type</label>
              <select
                id="edition_type"
                name="edition_type"
                value={formData.edition_type}
                onChange={handleChange}
              >
                <option value="">Select edition type...</option>
                {editionTypes.map((type) => (
                  <option key={type.code} value={type.code}>
                    {type.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="pressing_plant">Pressing Plant</label>
              <input
                type="text"
                id="pressing_plant"
                name="pressing_plant"
                value={formData.pressing_plant}
                onChange={handleChange}
                placeholder="EMI Hayes"
                maxLength={200}
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="mastering_studio">Mastering Studio</label>
              <input
                type="text"
                id="mastering_studio"
                name="mastering_studio"
                value={formData.mastering_studio}
                onChange={handleChange}
                placeholder="Abbey Road Studios"
                maxLength={200}
              />
            </div>

            <div className="form-group">
              <label htmlFor="mastering_engineer">Mastering Engineer</label>
              <input
                type="text"
                id="mastering_engineer"
                name="mastering_engineer"
                value={formData.mastering_engineer}
                onChange={handleChange}
                placeholder="Bob Ludwig"
                maxLength={200}
              />
            </div>

            <div className="form-group">
              <label htmlFor="label_design">Label Design</label>
              <input
                type="text"
                id="label_design"
                name="label_design"
                value={formData.label_design}
                onChange={handleChange}
                placeholder="Apple label"
                maxLength={200}
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="pressing_image_upload">Pressing Cover Image</label>
            <div className="image-upload">
              <div className="image-preview" aria-live="polite">
                {formData.pressing_image_url ? (
                  <img src={formData.pressing_image_url} alt={`${formData.title || 'Pressing'} preview`} />
                ) : (
                  <span>No image selected</span>
                )}
              </div>
              <div className="image-actions">
                <input
                  type="file"
                  id="pressing_image_upload"
                  name="pressing_image_upload"
                  accept="image/*"
                  onChange={handlePressingImageChange}
                />
                {formData.pressing_image_url && (
                  <button
                    type="button"
                    className="btn-secondary btn-image-remove"
                    onClick={handlePressingImageRemove}
                    disabled={loading}
                  >
                    Remove Image
                  </button>
                )}
              </div>
            </div>
            <small>PNG or JPG recommended. Smaller images load faster.</small>
          </div>

          <div className="form-group">
            <label htmlFor="barcode">Barcode and Other Identifiers</label>
            <textarea
              id="barcode"
              name="barcode"
              value={formData.barcode}
              onChange={handleChange}
              placeholder={"Barcode: 5099969945526\nMatrix / Runout (A): YEX 749-1\nMatrix / Runout (B): YEX 750-1\nCatalog Number: PCS 7088"}
              maxLength={2000}
            />
          </div>

          <div className="form-group">
            <label htmlFor="pressing_notes">Pressing Notes</label>
            <textarea
              id="pressing_notes"
              name="pressing_notes"
              value={formData.pressing_notes}
              onChange={handleChange}
              placeholder="Matrix info, pressing details..."
              rows={2}
            />
          </div>
        </>
      )}

      {addPressing && (!isWizardMode || wizardStep === 3) && (
        <>
          <h3>Add to Collection</h3>

          {!isWizardMode && (
            <div className="form-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={addToCollection}
                  onChange={(e) => setAddToCollection(e.target.checked)}
                />
                <span>Add this pressing to my collection</span>
              </label>
            </div>
          )}

          {addToCollection && (
            <>
              {/* Line 1: Purchase Date, Purchase Price (with Currency), Seller */}
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="purchase_date">Purchase Date</label>
                  <input
                    type="date"
                    id="purchase_date"
                    name="purchase_date"
                    value={formData.purchase_date}
                    onChange={handleChange}
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="purchase_price">Purchase Price</label>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{
                      padding: '0.75rem',
                      background: '#2a2a2a',
                      border: '1px solid var(--color-border-strong)',
                      borderRadius: '4px',
                      color: 'var(--color-text-muted)',
                      fontSize: '1rem',
                      minWidth: '60px',
                      textAlign: 'center'
                    }}>
                      {formData.purchase_currency || 'USD'}
                    </span>
                    <input
                      type="number"
                      id="purchase_price"
                      name="purchase_price"
                      value={formData.purchase_price}
                      onChange={handleChange}
                      placeholder="25.99"
                      step="0.01"
                      min="0"
                      style={{ flex: 1 }}
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label htmlFor="seller">Seller</label>
                  <input
                    type="text"
                    id="seller"
                    name="seller"
                    value={formData.seller}
                    onChange={handleChange}
                    placeholder="Record store name"
                    maxLength={200}
                  />
                </div>
              </div>

              {/* Line 2: Vinyl Condition, Sleeve Condition, Storage Location */}
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="media_condition">
                    Vinyl Condition <span className="required">*</span>
                  </label>
                  <select
                    id="media_condition"
                    name="media_condition"
                    value={formData.media_condition}
                    onChange={handleChange}
                    required={addToCollection}
                  >
                    {CONDITIONS.map((cond) => (
                      <option key={cond.value} value={cond.value}>
                        {cond.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label htmlFor="sleeve_condition">
                    Sleeve Condition <span className="required">*</span>
                  </label>
                  <select
                    id="sleeve_condition"
                    name="sleeve_condition"
                    value={formData.sleeve_condition}
                    onChange={handleChange}
                    required={addToCollection}
                  >
                    {CONDITIONS.map((cond) => (
                      <option key={cond.value} value={cond.value}>
                        {cond.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label htmlFor="location">Storage Location</label>
                  <input
                    type="text"
                    id="location"
                    name="location"
                    value={formData.location}
                    onChange={handleChange}
                    placeholder="Shelf A3"
                    maxLength={200}
                  />
                </div>
              </div>

              {/* Line 3: Defect Notes, Collection Notes (spanning columns) */}
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="defect_notes">Defect Notes</label>
                  <textarea
                    id="defect_notes"
                    name="defect_notes"
                    value={formData.defect_notes}
                    onChange={handleChange}
                    rows={2}
                    placeholder="Minor scuff on side B"
                  />
                </div>

                <div className="form-group" style={{ gridColumn: 'span 2' }}>
                  <label htmlFor="collection_notes">Collection Notes</label>
                  <textarea
                    id="collection_notes"
                    name="collection_notes"
                    value={formData.collection_notes}
                    onChange={handleChange}
                    rows={2}
                    placeholder="Personal notes about this copy"
                  />
                </div>
              </div>
            </>
          )}
        </>
      )}

      {!isWizardMode && (
        <div className="form-actions">
          <button
            type="button"
            onClick={onCancel}
            className="btn-secondary"
            disabled={loading}
          >
            Cancel
          </button>
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? 'Creating...' : (addPressing && addToCollection ? 'Create & Add to Collection' : 'Create Album')}
          </button>
        </div>
      )}
    </form>
  );
});
AlbumWithPressingForm.displayName = 'AlbumWithPressingForm';
