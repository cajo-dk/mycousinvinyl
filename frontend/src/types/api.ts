/**
 * TypeScript types matching backend API schemas.
 *
 * These types ensure type safety when working with API responses.
 */

// ============================================================================
// ENUMS (matching backend value objects)
// ============================================================================

export type ArtistType = string;
export type ReleaseType = string;

export enum VinylFormat {
  LP = 'LP',
  EP = 'EP',
  SINGLE = 'Single',
  MAXI = 'Maxi',
  CD = 'CD',
}

export enum VinylSpeed {
  RPM_33 = '33 1/3',
  RPM_45 = '45',
  RPM_78 = '78',
  NA = 'N/A',
}

export enum VinylSize {
  SIZE_7 = '7"',
  SIZE_10 = '10"',
  SIZE_12 = '12"',
  CD = 'CD',
}

export type EditionType = string;
export type SleeveType = string;

export enum Condition {
  MINT = 'Mint',
  NEAR_MINT = 'NM',
  VG_PLUS = 'VG+',
  VG = 'VG',
  GOOD = 'G',
  POOR = 'P',
}

export enum DataSource {
  USER = 'User',
  DISCOGS = 'Discogs',
  MUSICBRAINZ = 'MusicBrainz',
  MANUAL = 'Manual',
}

// ============================================================================
// COMMON TYPES
// ============================================================================

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface MessageResponse {
  message: string;
}

export interface ErrorResponse {
  detail: string;
}

// ============================================================================
// ARTIST TYPES
// ============================================================================

export interface ArtistCreate {
  name: string;
  sort_name?: string;
  artist_type: ArtistType;
  country?: string;
  disambiguation?: string;
  bio?: string;
  image_url?: string;
  begin_date?: string;
  end_date?: string;
  discogs_id?: number;
  data_source?: DataSource;
}

export interface ArtistUpdate {
  name?: string;
  sort_name?: string;
  artist_type?: ArtistType;
  country?: string;
  disambiguation?: string;
  bio?: string;
  image_url?: string | null;
  begin_date?: string;
  end_date?: string;
  discogs_id?: number;
}

export interface ArtistResponse {
  id: string;
  name: string;
  sort_name?: string;
  artist_type: ArtistType;
  type?: ArtistType;
  country?: string;
  disambiguation?: string;
  bio?: string;
  image_url?: string;
  begin_date?: string;
  end_date?: string;
  discogs_id?: number;
  album_count?: number;
  data_source: DataSource;
  created_at: string;
  updated_at: string;
}

export interface ArtistSummary {
  id: string;
  name: string;
  artist_type: ArtistType;
  country?: string;
  image_url?: string;
}

// ============================================================================
// DISCOGS TYPES
// ============================================================================

export interface DiscogsArtistSearchResult {
  id: number;
  name: string;
  thumb_url?: string;
  uri?: string;
  resource_url?: string;
}

export interface DiscogsArtistSearchResponse {
  items: DiscogsArtistSearchResult[];
}

export interface DiscogsArtistDetails {
  id: number;
  name: string;
  bio?: string;
  country?: string;
  begin_date?: string;
  end_date?: string;
  sort_name?: string;
  image_url?: string;
  artist_type?: string;
}

export interface DiscogsAlbumSearchResult {
  id: number;
  title: string;
  year?: number;
  type?: string;
  thumb_url?: string;
  resource_url?: string;
}

export interface DiscogsAlbumSearchResponse {
  items: DiscogsAlbumSearchResult[];
  total?: number;
  page?: number;
  pages?: number;
}

export interface DiscogsAlbumDetails {
  id: number;
  title: string;
  year?: number;
  country?: string;
  genres?: string[];
  styles?: string[];
  label?: string;
  catalog_number?: string;
  image_url?: string;
  type?: string;
}

export interface DiscogsReleaseSearchResult {
  id: number;
  title: string;
  year?: number;
  country?: string;
  label?: string;
  catalog_number?: string;
  format?: string;
  barcode?: string;
  identifiers?: string;
  type: string;
  master_id?: number;
  master_title?: string;
  thumb_url?: string;
  resource_url?: string;
}

export interface DiscogsReleaseSearchResponse {
  items: DiscogsReleaseSearchResult[];
  total?: number;
  page?: number;
  pages?: number;
}

export interface DiscogsReleaseDetails {
  id: number;
  title: string;
  year?: number;
  country?: string;
  label?: string;
  catalog_number?: string;
  barcode?: string;
  identifiers?: string;
  image_url?: string;
  formats?: string[];
  format_descriptions?: string[];
  disc_count?: number;
  master_id?: number;
  master_title?: string;
  pressing_plant?: string;
  mastering_engineer?: string;
  mastering_studio?: string;
  vinyl_color?: string;
  edition_type?: string;
  sleeve_type?: string;
}

export interface DiscogsOAuthStartRequest {
  redirect_uri?: string;
}

export interface DiscogsOAuthStartResponse {
  authorization_url: string;
}

export interface DiscogsOAuthStatusResponse {
  connected: boolean;
  username?: string;
  last_synced_at?: string | null;
}

export interface DiscogsPatConnectRequest {
  username: string;
  token: string;
}

// ============================================================================
// GENRE / STYLE / COUNTRY TYPES
// ============================================================================

export interface GenreResponse {
  id: string;
  name: string;
  display_order?: number;
  created_at: string;
}

export interface StyleResponse {
  id: string;
  name: string;
  genre_id?: string;
  display_order?: number;
  created_at: string;
}

export interface CountryResponse {
  code: string;
  name: string;
  display_order?: number;
  created_at: string;
}

export interface ArtistTypeResponse {
  code: string;
  name: string;
  display_order?: number;
  created_at: string;
}

export interface ReleaseTypeResponse {
  code: string;
  name: string;
  display_order?: number;
  created_at: string;
}

export interface EditionTypeResponse {
  code: string;
  name: string;
  display_order?: number;
  created_at: string;
}

export interface SleeveTypeResponse {
  code: string;
  name: string;
  display_order?: number;
  created_at: string;
}

// ============================================================================
// ALBUM TYPES
// ============================================================================

export interface AlbumCreate {
  title: string;
  artist_id: string;
  release_type: ReleaseType;
  release_year?: number;
  country_of_origin?: string;
  genre_ids?: string[];
  style_ids?: string[];
  label?: string;
  catalog_number?: string;
  barcode?: string;
  notes?: string;
  image_url?: string;
  discogs_id?: number;
  data_source?: DataSource;
}

export interface AlbumUpdate {
  title?: string;
  artist_id?: string;
  release_type?: ReleaseType;
  release_year?: number;
  country_of_origin?: string;
  genre_ids?: string[];
  style_ids?: string[];
  label?: string;
  catalog_number?: string;
  barcode?: string;
  notes?: string;
  image_url?: string | null;
  discogs_id?: number;
}

export interface AlbumResponse {
  id: string;
  title: string;
  artist_id: string;
  primary_artist_id?: string;
  release_type: ReleaseType;
  release_year?: number;
  original_release_year?: number;
  country_of_origin?: string;
  genre_ids: string[];
  style_ids: string[];
  label?: string;
  catalog_number?: string;
  catalog_number_base?: string;
  barcode?: string;
  notes?: string;
  description?: string;
  image_url?: string;
  discogs_id?: number;
  data_source: DataSource;
  created_at: string;
  updated_at: string;
  genres: GenreResponse[];
  styles: StyleResponse[];
}

export interface AlbumSummary {
  id: string;
  title: string;
  artist_id: string;
  release_year?: number;
  release_type: ReleaseType;
}

export interface ArtistSummaryForAlbum {
  id: string;
  name: string;
  sort_name?: string;
  artist_type: ArtistType;
}

export interface AlbumDetailResponse {
  id: string;
  title: string;
  artist_id: string;
  release_year?: number;
  release_type: ReleaseType;
  label?: string;
  catalog_number?: string;
  image_url?: string;
  discogs_id?: number;
  genres: string[];
  styles: string[];
  pressing_count: number;
  in_user_collection?: boolean; // DEPRECATED: Use owners instead
  owners?: UserOwnerInfo[];
  created_at: string;
  updated_at: string;
  artist: ArtistSummaryForAlbum;
}

// ============================================================================
// TRACK TYPES
// ============================================================================

export interface TrackCreate {
  album_id: string;
  side: string;
  position: string;
  title: string;
  duration?: number;
  credits?: string;
}

export interface TrackUpdate {
  side?: string;
  position?: string;
  title?: string;
  duration?: number;
  credits?: string;
}

export interface TrackResponse {
  album_id: string;
  side: string;
  position: string;
  title: string;
  duration?: number;
  credits?: string;
  created_at: string;
  updated_at: string;
}

// ============================================================================
// PRESSING TYPES
// ============================================================================

export interface MatrixResponse {
  id: string;
  pressing_id: string;
  side: string;
  matrix_code?: string;
  etchings?: string;
  stamper_info?: string;
  created_at: string;
}

export interface PackagingResponse {
  id: string;
  pressing_id: string;
  sleeve_type: SleeveType;
  has_inner_sleeve: boolean;
  inner_sleeve_description?: string;
  has_insert: boolean;
  insert_description?: string;
  has_poster: boolean;
  poster_description?: string;
  sticker_info?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface PackagingCreateOrUpdate {
  pressing_id: string;
  sleeve_type: SleeveType;
  has_inner_sleeve?: boolean;
  inner_sleeve_description?: string;
  has_insert?: boolean;
  insert_description?: string;
  has_poster?: boolean;
  poster_description?: string;
  sticker_info?: string;
  notes?: string;
}

export interface PressingCreate {
  album_id: string;
  format: VinylFormat;
  speed_rpm: VinylSpeed;
  size_inches: VinylSize;
  disc_count?: number;
  country?: string;
  release_year?: number;
  pressing_plant?: string;
  mastering_engineer?: string;
  mastering_studio?: string;
  vinyl_color?: string;
  label_design?: string;
  image_url?: string;
  edition_type?: EditionType;
  barcode?: string;
  notes?: string;
  discogs_release_id?: number;
  discogs_master_id?: number;
  master_title?: string;
  import_master_releases?: boolean;
}

export interface PressingUpdate {
  format?: VinylFormat;
  speed_rpm?: VinylSpeed;
  size_inches?: VinylSize;
  disc_count?: number;
  country?: string;
  release_year?: number;
  pressing_plant?: string;
  mastering_engineer?: string;
  mastering_studio?: string;
  vinyl_color?: string;
  label_design?: string;
  image_url?: string | null;
  edition_type?: EditionType;
  barcode?: string;
  notes?: string;
  discogs_release_id?: number | null;
  discogs_master_id?: number | null;
  master_title?: string | null;
}

export interface PressingResponse {
  id: string;
  album_id: string;
  format: VinylFormat;
  speed_rpm: VinylSpeed;
  size_inches: VinylSize;
  disc_count: number;
  country?: string;
  pressing_country?: string;
  release_year?: number;
  pressing_year?: number;
  pressing_plant?: string;
  mastering_engineer?: string;
  mastering_studio?: string;
  vinyl_color?: string;
  label_design?: string;
  image_url?: string;
  edition_type?: EditionType;
  barcode?: string;
  notes?: string;
  discogs_release_id?: number;
  discogs_master_id?: number;
  master_title?: string;
  is_master?: boolean;
  created_by?: string;
  created_at: string;
  updated_at: string;
  matrices: MatrixResponse[];
  packaging?: PackagingResponse;
  in_user_collection?: boolean; // DEPRECATED: Use owners instead
  owners?: UserOwnerInfo[];
}

export interface ArtistSummaryForPressing {
  id: string;
  name: string;
  sort_name?: string;
  discogs_id?: number | null;
}

export interface AlbumSummaryForPressing {
  id: string;
  title: string;
  release_year?: number;
  image_url?: string;
  discogs_id?: number | null;
}

export interface PressingDetailResponse {
  id: string;
  album_id: string;
  format: VinylFormat;
  speed_rpm: VinylSpeed;
  size_inches: VinylSize;
  disc_count: number;
  country?: string;
  release_year?: number;
  pressing_plant?: string;
  vinyl_color?: string;
  edition_type?: EditionType;
  sleeve_type?: SleeveType;
  barcode?: string;
  notes?: string;
  image_url?: string;
  discogs_release_id?: number;
  discogs_master_id?: number;
  master_title?: string;
  is_master?: boolean;
  created_at: string;
  updated_at: string;
  artist: ArtistSummaryForPressing;
  album: AlbumSummaryForPressing;
  in_user_collection?: boolean; // DEPRECATED: Use owners instead
  owners?: UserOwnerInfo[];
}

// ============================================================================
// COLLECTION TYPES
// ============================================================================

export interface CollectionItemCreate {
  pressing_id: string;
  media_condition: Condition;
  sleeve_condition: Condition;
  purchase_price?: number;
  purchase_currency?: string;
  purchase_date?: string;
  seller?: string;
  location?: string;
  defect_notes?: string;
  notes?: string;
}

export interface CollectionItemUpdate {
  media_condition?: Condition;
  sleeve_condition?: Condition;
  purchase_price?: number;
  purchase_currency?: string;
  purchase_date?: string;
  seller?: string;
  location?: string;
  defect_notes?: string;
  notes?: string;
}

export interface CollectionItemResponse {
  id: string;
  user_id: string;
  pressing_id: string;
  media_condition: Condition;
  sleeve_condition: Condition;
  purchase_price?: number;
  purchase_currency?: string;
  purchase_date?: string;
  seller?: string;
  location?: string;
  defect_notes?: string;
  notes?: string;
  rating?: number;
  play_count: number;
  last_played?: string;
  date_added: string;
  updated_at: string;
}

export interface CollectionArtistSummary {
  id: string;
  name: string;
  sort_name?: string;
  country?: string;
}

export interface CollectionAlbumSummary {
  id: string;
  title: string;
  release_year?: number;
  genres: string[];
  image_url?: string;
}

export interface MarketDataSummary {
  min_value: number | null;
  median_value: number | null;
  max_value: number | null;
  currency: string | null;
  updated_at: string | null;
}

export interface CollectionItemDetailResponse {
  id: string;
  user_id: string;
  pressing_id: string;
  pressing_image_url?: string;
  media_condition: Condition;
  sleeve_condition: Condition;
  purchase_price?: number;
  purchase_currency?: string;
  purchase_date?: string;
  seller?: string;
  location?: string;
  defect_notes?: string;
  notes?: string;
  rating?: number;
  play_count: number;
  last_played?: string;
  date_added: string;
  updated_at: string;
  artist: CollectionArtistSummary;
  album: CollectionAlbumSummary;
  market_data: MarketDataSummary | null;
}

export interface CollectionStatistics {
  total_albums: number;
  total_purchase_price: number;
  min_value: number;
  avg_value: number;
  max_value: number;
  low_est_sales_price: number;
  avg_est_sales_price: number;
  high_est_sales_price: number;
  currency: string;
  top_artists: TopArtistEntry[];
  top_albums: TopAlbumEntry[];
}

export interface AlbumPlayIncrementResponse {
  album_id: string;
  play_count: number;
  play_count_ytd: number;
  last_played_at: string;
}

export interface PlayedAlbumEntry {
  album_id: string;
  album_title: string;
  artist_id: string;
  artist_name: string;
  play_count_ytd: number;
  last_played_at?: string | null;
}

export interface TopArtistEntry {
  artist_id: string;
  artist_name: string;
  collected_count: number;
}

export interface TopAlbumEntry {
  album_id: string;
  album_title: string;
  artist_id: string;
  artist_name: string;
  collected_count: number;
}

export interface CollectionImportResponse {
  id: string;
  filename: string;
  status: string;
  total_rows: number;
  processed_rows: number;
  success_count: number;
  error_count: number;
  started_at?: string | null;
  completed_at?: string | null;
  error_summary?: string | null;
  rows?: CollectionImportRowResponse[] | null;
}

export interface CollectionImportRowResponse {
  row_number: number;
  result: string;
  message: string;
  discogs_release_id?: number | null;
  artist?: string | null;
  title?: string | null;
}

// ============================================================================
// PREFERENCES TYPES
// ============================================================================

// ============================================================================
// COLLECTION SHARING TYPES
// ============================================================================

export interface CollectionSharingSettings {
  enabled: boolean;
  icon_type: string;
  icon_fg_color: string;
  icon_bg_color: string;
}

export interface UserOwnerInfo {
  user_id: string;
  display_name: string;
  first_name: string;
  icon_type: string;
  icon_fg_color: string;
  icon_bg_color: string;
  copy_count: number;
}

export interface FollowUserRequest {
  user_id: string;
}

export interface FollowsListResponse {
  follows: UserOwnerInfo[];
  count: number;
}

export interface UserSearchResponse {
  users: UserOwnerInfo[];
  count: number;
}

export interface ItemOwnersResponse {
  owners: UserOwnerInfo[];
}

export interface PressingOwnersBatchResponse {
  owners_by_pressing: Record<string, UserOwnerInfo[]>;
}

export interface AlbumOwnersBatchResponse {
  owners_by_album: Record<string, UserOwnerInfo[]>;
}

// ============================================================================
// ALBUM WIZARD TYPES
// ============================================================================

export interface AlbumWizardScanRequest {
  image_data_url: string;
}

export interface AlbumWizardAiResult {
  artist: string;
  album: string;
  image: boolean;
  artist_confidence?: number;
  album_confidence?: number;
  combined_confidence?: number;
  popular_artist?: string;
  popular_album?: string;
}

export type AlbumWizardMatchStatus =
  | 'no_image'
  | 'no_artist_match'
  | 'no_album_match'
  | 'match_found';

export interface AlbumWizardArtistMatch {
  id: string;
  name: string;
  sort_name?: string;
  artist_type: ArtistType;
}

export interface AlbumWizardAlbumMatch {
  id: string;
  title: string;
  release_year?: number;
  image_url?: string;
}

export interface AlbumWizardScanResponse {
  ai_result: AlbumWizardAiResult;
  match_status: AlbumWizardMatchStatus;
  matched_artist?: AlbumWizardArtistMatch | null;
  matched_album?: AlbumWizardAlbumMatch | null;
  owners?: UserOwnerInfo[];
  message?: string;
}

// ============================================================================
// USER PREFERENCES
// ============================================================================

export interface PreferencesResponse {
  user_id: string;
  currency: string;
  display_settings: Record<string, any>;
  collection_sharing: CollectionSharingSettings;
  created_at: string;
  updated_at: string;
}

export interface PreferencesUpdate {
  currency?: string;
  display_settings?: Record<string, any>;
}
