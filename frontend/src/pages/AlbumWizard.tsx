/**
 * Album Wizard page - scan album covers on mobile to check ownership.
 */

import { useEffect, useRef, useState } from 'react';
import { useMsal } from '@azure/msal-react';
import { albumWizardApi } from '@/api/services';
import { AlbumWizardScanResponse } from '@/types/api';
import { OwnersGrid } from '@/components/CollectionSharing';
import { Icon, Loading } from '@/components/UI';
import { mdiCamera, mdiCheck, mdiRefresh } from '@mdi/js';
import './AlbumWizard.css';

export function AlbumWizard() {
  const { accounts } = useMsal();
  const currentUserId = (accounts[0]?.idTokenClaims?.oid as string) || accounts[0]?.localAccountId || '';
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [photoDataUrl, setPhotoDataUrl] = useState<string | null>(null);
  const [scanResult, setScanResult] = useState<AlbumWizardScanResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loadingCamera, setLoadingCamera] = useState(true);
  const [isScanning, setIsScanning] = useState(false);

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      setStream(null);
    }
  };

  const startCamera = async () => {
    setLoadingCamera(true);
    setError(null);
    try {
      if (!navigator.mediaDevices?.getUserMedia) {
        throw new Error('Camera access is not supported on this device.');
      }
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' },
        audio: false,
      });
      setStream(mediaStream);
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
        await videoRef.current.play();
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to access camera.');
    } finally {
      setLoadingCamera(false);
    }
  };

  useEffect(() => {
    startCamera();
    return () => stopCamera();
  }, []);

  useEffect(() => {
    document.body.classList.add('album-wizard-portrait');
    return () => {
      document.body.classList.remove('album-wizard-portrait');
    };
  }, []);

  const handleCapture = () => {
    if (!videoRef.current || !canvasRef.current) return;
    const video = videoRef.current;
    const canvas = canvasRef.current;
    const context = canvas.getContext('2d');
    if (!context) return;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    const dataUrl = canvas.toDataURL('image/jpeg', 0.9);
    setPhotoDataUrl(dataUrl);
    setScanResult(null);
    stopCamera();
  };

  const handleRetake = () => {
    setPhotoDataUrl(null);
    setScanResult(null);
    startCamera();
  };

  const handleScan = async () => {
    if (!photoDataUrl) return;
    setIsScanning(true);
    setError(null);
    try {
      const result = await albumWizardApi.scanAlbum(photoDataUrl);
      setScanResult(result);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to scan album.');
    } finally {
      setIsScanning(false);
    }
  };

  const titleCaseAlbum = (value: string) => {
    const lowerWords = new Set(['a', 'an', 'and', 'as', 'at', 'but', 'by', 'for', 'from', 'in', 'nor', 'of', 'on', 'or', 'to', 'with']);
    return value
      .split(' ')
      .filter(Boolean)
      .map((word, index, all) => {
        const lower = word.toLowerCase();
        const isEdge = index === 0 || index === all.length - 1;
        if (!isEdge && lowerWords.has(lower)) {
          return lower;
        }
        return lower.charAt(0).toUpperCase() + lower.slice(1);
      })
      .join(' ');
  };

  const rawArtist = scanResult?.matched_artist?.name || scanResult?.ai_result?.artist || '---';
  const rawAlbum = scanResult?.matched_album?.title || scanResult?.ai_result?.album || '---';
  const aiAlbumConfidence = scanResult?.ai_result?.album_confidence;
  const displayArtist = (() => {
    if (rawArtist === '---') return rawArtist;
    if (typeof scanResult?.ai_result?.artist_confidence === 'number') {
      return `${rawArtist} (${scanResult.ai_result.artist_confidence.toFixed(2)})`;
    }
    return rawArtist;
  })();
  const displayAlbum = (() => {
    if (rawAlbum === '---') return rawAlbum;
    let albumTitle = rawAlbum;
    if (!scanResult?.matched_album && rawArtist !== '---' && rawAlbum.includes(' - ')) {
      const [candidateArtist, ...rest] = rawAlbum.split(' - ');
      if (candidateArtist.trim().toLowerCase() === rawArtist.trim().toLowerCase()) {
        albumTitle = rest.join(' - ').trim();
      }
    }
    if (!scanResult?.matched_album) {
      albumTitle = titleCaseAlbum(albumTitle);
    }
    if (typeof aiAlbumConfidence === 'number') {
      return `${albumTitle} (${aiAlbumConfidence.toFixed(2)})`;
    }
    return albumTitle;
  })();
  const showOwners = scanResult?.match_status === 'match_found';

  return (
    <div className="album-wizard-page">
      <header className="album-wizard-header">
        <div>
        </div>
      </header>

      <section className="album-wizard-camera">
        <div className="camera-frame">
          {photoDataUrl ? (
            <img src={photoDataUrl} alt="Captured album cover" />
          ) : (
            <video ref={videoRef} playsInline muted />
          )}
          {isScanning && photoDataUrl && (
            <div className="camera-overlay">
              <Loading message="Processing photo..." />
            </div>
          )}
          {loadingCamera && !photoDataUrl && (
            <div className="camera-overlay">
              <Loading message="Starting camera..." />
            </div>
          )}
        </div>

        <div className="camera-actions">
          {!loadingCamera && !isScanning && !photoDataUrl && (
            <button type="button" className="btn-primary" onClick={handleCapture}>
              <Icon path={mdiCamera} size={20} /> Capture
            </button>
          )}
          {!loadingCamera && !isScanning && photoDataUrl && (
            <>
              <button type="button" className="btn-secondary" onClick={handleRetake}>
                <Icon path={mdiRefresh} size={18} /> Retake
              </button>
              <button type="button" className="btn-primary" onClick={handleScan}>
                <Icon path={mdiCheck} size={18} /> Use Photo
              </button>
            </>
          )}
        </div>
      </section>

      {error && <div className="album-wizard-error">{error}</div>}

      <section className="album-wizard-results">
        <div className="result-row">
          <span className="result-label">Found Artist</span>
          <span className="result-value">{displayArtist}</span>
        </div>
        <div className="result-row">
          <span className="result-label">Found Album</span>
          <span className="result-value">{displayAlbum}</span>
        </div>
        {scanResult?.message && (
          <div className="result-message">{scanResult.message}</div>
        )}
      </section>

      <section className="album-wizard-owners">
        <div className="owners-header">
          <h2>Owners</h2>
          {!showOwners && <span>Scan an album to see owners</span>}
        </div>
        <div className="owners-grid-wrapper">
          <OwnersGrid
            owners={scanResult?.owners || []}
            currentUserId={currentUserId}
            showEmpty
            className="owners-grid-large owners-grid-row"
          />
        </div>
      </section>

      <canvas ref={canvasRef} className="hidden-canvas" />
    </div>
  );
}
