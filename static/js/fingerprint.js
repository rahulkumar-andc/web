(function() {
    'use strict';
    
    const FINGERPRINT_STORAGE_KEY = 'vsc_device_seed';
    
    function getOrCreateDeviceSeed() {
        let seed = localStorage.getItem(FINGERPRINT_STORAGE_KEY);
        if (!seed) {
            seed = generateRandomSeed();
            localStorage.setItem(FINGERPRINT_STORAGE_KEY, seed);
        }
        return seed;
    }
    
    function generateRandomSeed() {
        const array = new Uint8Array(32);
        crypto.getRandomValues(array);
        return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
    }
    
    function getCanvasFingerprint() {
        try {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            canvas.width = 200;
            canvas.height = 50;
            ctx.textBaseline = 'top';
            ctx.font = '14px Arial';
            ctx.fillStyle = '#f60';
            ctx.fillRect(50, 0, 100, 50);
            ctx.fillStyle = '#069';
            ctx.fillText('VillenSec', 2, 15);
            ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
            ctx.fillText('VillenSec', 4, 17);
            return canvas.toDataURL();
        } catch (e) {
            return '';
        }
    }
    
    function getWebGLInfo() {
        try {
            const canvas = document.createElement('canvas');
            const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
            if (!gl) return { vendor: '', renderer: '' };
            
            const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
            if (!debugInfo) return { vendor: '', renderer: '' };
            
            return {
                vendor: gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL) || '',
                renderer: gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) || ''
            };
        } catch (e) {
            return { vendor: '', renderer: '' };
        }
    }
    
    function getBrowserInfo() {
        const ua = navigator.userAgent;
        let browser = 'Unknown';
        let os = 'Unknown';
        let deviceType = 'Desktop';
        
        if (/mobile/i.test(ua) || /android/i.test(ua) || /iphone/i.test(ua)) {
            deviceType = 'Mobile';
        } else if (/tablet/i.test(ua) || /ipad/i.test(ua)) {
            deviceType = 'Tablet';
        }
        
        if (/chrome/i.test(ua) && !/edg/i.test(ua)) {
            browser = 'Chrome';
        } else if (/firefox/i.test(ua)) {
            browser = 'Firefox';
        } else if (/safari/i.test(ua) && !/chrome/i.test(ua)) {
            browser = 'Safari';
        } else if (/edg/i.test(ua)) {
            browser = 'Edge';
        }
        
        if (/windows/i.test(ua)) {
            os = 'Windows';
        } else if (/macintosh|mac os/i.test(ua)) {
            os = 'macOS';
        } else if (/linux/i.test(ua) && !/android/i.test(ua)) {
            os = 'Linux';
        } else if (/android/i.test(ua)) {
            os = 'Android';
        } else if (/iphone|ipad/i.test(ua)) {
            os = 'iOS';
        }
        
        return { browser, os, deviceType };
    }
    
    function collectFingerprint() {
        const webgl = getWebGLInfo();
        const browserInfo = getBrowserInfo();
        
        const fingerprintData = {
            seed: getOrCreateDeviceSeed(),
            userAgent: navigator.userAgent,
            language: navigator.language,
            languages: navigator.languages ? navigator.languages.join(',') : '',
            platform: navigator.platform || '',
            hardwareConcurrency: navigator.hardwareConcurrency || 0,
            deviceMemory: navigator.deviceMemory || 0,
            screenWidth: screen.width,
            screenHeight: screen.height,
            screenColorDepth: screen.colorDepth,
            screenPixelRatio: window.devicePixelRatio || 1,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            timezoneOffset: new Date().getTimezoneOffset(),
            webglVendor: webgl.vendor,
            webglRenderer: webgl.renderer,
            canvas: getCanvasFingerprint(),
            touchSupport: 'ontouchstart' in window,
            cookiesEnabled: navigator.cookieEnabled,
        };
        
        const metadata = {
            browser: browserInfo.browser,
            os: browserInfo.os,
            device_type: browserInfo.deviceType,
            screen: `${screen.width}x${screen.height}`,
            language: navigator.language,
            timezone: fingerprintData.timezone
        };
        
        return {
            data: fingerprintData,
            metadata: metadata
        };
    }
    
    async function hashFingerprint(data) {
        const str = JSON.stringify(data);
        const encoder = new TextEncoder();
        const dataBuffer = encoder.encode(str);
        const hashBuffer = await crypto.subtle.digest('SHA-256', dataBuffer);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    }
    
    async function getDeviceFingerprint() {
        const fingerprint = collectFingerprint();
        const hash = await hashFingerprint(fingerprint.data);
        return {
            hash: hash,
            metadata: fingerprint.metadata
        };
    }
    
    function setFingerprintField(fingerprint) {
        const hashField = document.getElementById('device_fingerprint');
        const metadataField = document.getElementById('device_metadata');
        
        if (hashField) {
            hashField.value = fingerprint.hash;
        }
        if (metadataField) {
            metadataField.value = JSON.stringify(fingerprint.metadata);
        }
    }
    
    async function initFingerprint() {
        try {
            const fingerprint = await getDeviceFingerprint();
            setFingerprintField(fingerprint);
            window.VillenSecFingerprint = fingerprint;
        } catch (e) {
            console.error('Fingerprint collection failed:', e);
        }
    }
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initFingerprint);
    } else {
        initFingerprint();
    }
    
    window.VillenSecFingerprintAPI = {
        getFingerprint: getDeviceFingerprint,
        refreshFingerprint: initFingerprint
    };
})();
