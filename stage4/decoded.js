$ = '<b>Failed to load stage5</b>';
useragent = window.navigator.userAgent;
document.write('<h1>Download manager</h1>');
document.write('<div id="status"><i>loading...</i></div>');
document.write('<div style="display:none"><a target="blank"' +
    ' href="chrome://browser/content/preferences/preferences.xul">' +
    'Back to preferences</a></div>');


/* Convert a string to an Uint8Array */
function str_to_u8arr(v6) {
    _ = [];
    for (v11 = 0; v11 < v6.length; ++v11)
        _.push(v6.charCodeAt(v11));
    return new Uint8Array(_);
}
/* Decode an hexadecimal string to an Uint8Array */
function hexstr_to_u8arr(v6) {
    _ = [];
    for (v11 = 0; v11 < v6.length / 2; ++v11)
        _.push(parseInt(v6.substr(v11 * 2, 2), 16));
    return new Uint8Array(_);
}
/* Encode an Uint8Array to an hexadecimal string */
function u8arr_to_hexstr(v8) {
    v6 = '';
    for (v11 = 0; v11 < v8.byteLength; ++v11) {
         v3 = v8[v11].toString(16);
         if (v3.length < 2)
            v6 += 0;
         v6 += v3;
    }
    return v6;
}

function v27() {
    iv = str_to_u8arr(useragent.substr(useragent.indexOf('(') + 1, 16));
    key = str_to_u8arr(useragent.substr(useragent.indexOf(')') - 16, 16));
    _$ = {};
    _$['name'] = 'AES-CBC';
    _$['iv'] = iv;
    _$['length'] = key.length * 8;
    window.crypto.subtle.importKey("raw", key, _$, false, ['decrypt'])
    .then(function(importedKey) {
        window.crypto.subtle.decrypt(_$, importedKey, hexstr_to_u8arr(data))
        .then(function(result) {
            decrypted = new Uint8Array(result);
            window.crypto.subtle.digest({name: 'SHA-1'}, decrypted)
            .then(function(digest) {
                if (hash == u8arr_to_hexstr(new Uint8Array(digest))) {
                    myBlobAttributes = {};
                    myBlobAttributes['type'] = 'application/octet-stream';
                    myBlob = new Blob([decrypted], myBlobAttributes);
                    myURL = URL.createObjectURL(myBlob);
                    document.getElementById('status').innerHTML =
                        '<a href="' + myURL + '" download="stage5.zip">' +
                        'download stage5</a>';
                } else {
                    document.getElementById('status').innerHTML = $;
                }
            });
        }).catch(function() {
            document.getElementById('status').innerHTML = $;
        });
    }).catch(function() {
        document.getElementById('status').innerHTML = $;
    });
}
window.setTimeout(v27, 1000);
