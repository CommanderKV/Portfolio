# ---------------------------------------------------------------------------
#     Code obtained from https://github.com/ozh/github-colors/tree/master
#     I do not take any credit for this code, I used it to get the colors 
#                 of all the programming languages on GitHub.
#
#     I have modified the code to return the json instead of writing it.
#             I have also added logging to the code with logfire.
#
#        Added code to return a svg along with the other color data.
# ---------------------------------------------------------------------------
import json
import requests
import sys
import yaml
try:
    from urllib import quote
except ImportError:
    from urllib.parse import quote
from collections import OrderedDict
import logfire

SVGS = {
    "python": """
            <svg viewBox="0 0 128 128">
            <linearGradient id="python-original-a" gradientUnits="userSpaceOnUse" x1="70.252" y1="1237.476" x2="170.659" y2="1151.089" gradientTransform="matrix(.563 0 0 -.568 -29.215 707.817)"><stop offset="0" stop-color="#5A9FD4"></stop><stop offset="1" stop-color="#306998"></stop></linearGradient><linearGradient id="python-original-b" gradientUnits="userSpaceOnUse" x1="209.474" y1="1098.811" x2="173.62" y2="1149.537" gradientTransform="matrix(.563 0 0 -.568 -29.215 707.817)"><stop offset="0" stop-color="#FFD43B"></stop><stop offset="1" stop-color="#FFE873"></stop></linearGradient><path fill="url(#python-original-a)" d="M63.391 1.988c-4.222.02-8.252.379-11.8 1.007-10.45 1.846-12.346 5.71-12.346 12.837v9.411h24.693v3.137H29.977c-7.176 0-13.46 4.313-15.426 12.521-2.268 9.405-2.368 15.275 0 25.096 1.755 7.311 5.947 12.519 13.124 12.519h8.491V67.234c0-8.151 7.051-15.34 15.426-15.34h24.665c6.866 0 12.346-5.654 12.346-12.548V15.833c0-6.693-5.646-11.72-12.346-12.837-4.244-.706-8.645-1.027-12.866-1.008zM50.037 9.557c2.55 0 4.634 2.117 4.634 4.721 0 2.593-2.083 4.69-4.634 4.69-2.56 0-4.633-2.097-4.633-4.69-.001-2.604 2.073-4.721 4.633-4.721z" transform="translate(0 10.26)"></path><path fill="url(#python-original-b)" d="M91.682 28.38v10.966c0 8.5-7.208 15.655-15.426 15.655H51.591c-6.756 0-12.346 5.783-12.346 12.549v23.515c0 6.691 5.818 10.628 12.346 12.547 7.816 2.297 15.312 2.713 24.665 0 6.216-1.801 12.346-5.423 12.346-12.547v-9.412H63.938v-3.138h37.012c7.176 0 9.852-5.005 12.348-12.519 2.578-7.735 2.467-15.174 0-25.096-1.774-7.145-5.161-12.521-12.348-12.521h-9.268zM77.809 87.927c2.561 0 4.634 2.097 4.634 4.692 0 2.602-2.074 4.719-4.634 4.719-2.55 0-4.633-2.117-4.633-4.719 0-2.595 2.083-4.692 4.633-4.692z" transform="translate(0 10.26)"></path><radialGradient id="python-original-c" cx="1825.678" cy="444.45" r="26.743" gradientTransform="matrix(0 -.24 -1.055 0 532.979 557.576)" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#B8B8B8" stop-opacity=".498"></stop><stop offset="1" stop-color="#7F7F7F" stop-opacity="0"></stop></radialGradient><path opacity=".444" fill="url(#python-original-c)" d="M97.309 119.597c0 3.543-14.816 6.416-33.091 6.416-18.276 0-33.092-2.873-33.092-6.416 0-3.544 14.815-6.417 33.092-6.417 18.275 0 33.091 2.872 33.091 6.417z"></path>
            </svg>
        """,
    "javascript": """
            <svg viewBox="0 0 128 128">
            <path fill="#F0DB4F" d="M1.408 1.408h125.184v125.185H1.408z"></path><path fill="#323330" d="M116.347 96.736c-.917-5.711-4.641-10.508-15.672-14.981-3.832-1.761-8.104-3.022-9.377-5.926-.452-1.69-.512-2.642-.226-3.665.821-3.32 4.784-4.355 7.925-3.403 2.023.678 3.938 2.237 5.093 4.724 5.402-3.498 5.391-3.475 9.163-5.879-1.381-2.141-2.118-3.129-3.022-4.045-3.249-3.629-7.676-5.498-14.756-5.355l-3.688.477c-3.534.893-6.902 2.748-8.877 5.235-5.926 6.724-4.236 18.492 2.975 23.335 7.104 5.332 17.54 6.545 18.873 11.531 1.297 6.104-4.486 8.08-10.234 7.378-4.236-.881-6.592-3.034-9.139-6.949-4.688 2.713-4.688 2.713-9.508 5.485 1.143 2.499 2.344 3.63 4.26 5.795 9.068 9.198 31.76 8.746 35.83-5.176.165-.478 1.261-3.666.38-8.581zM69.462 58.943H57.753l-.048 30.272c0 6.438.333 12.34-.714 14.149-1.713 3.558-6.152 3.117-8.175 2.427-2.059-1.012-3.106-2.451-4.319-4.485-.333-.584-.583-1.036-.667-1.071l-9.52 5.83c1.583 3.249 3.915 6.069 6.902 7.901 4.462 2.678 10.459 3.499 16.731 2.059 4.082-1.189 7.604-3.652 9.448-7.401 2.666-4.915 2.094-10.864 2.07-17.444.06-10.735.001-21.468.001-32.237z"></path>
            </svg>
        """,
    "java": """
            <svg viewBox="0 0 128 128">
            <path fill="#0074BD" d="M47.617 98.12s-4.767 2.774 3.397 3.71c9.892 1.13 14.947.968 25.845-1.092 0 0 2.871 1.795 6.873 3.351-24.439 10.47-55.308-.607-36.115-5.969zm-2.988-13.665s-5.348 3.959 2.823 4.805c10.567 1.091 18.91 1.18 33.354-1.6 0 0 1.993 2.025 5.132 3.131-29.542 8.64-62.446.68-41.309-6.336z"></path><path fill="#EA2D2E" d="M69.802 61.271c6.025 6.935-1.58 13.17-1.58 13.17s15.289-7.891 8.269-17.777c-6.559-9.215-11.587-13.792 15.635-29.58 0 .001-42.731 10.67-22.324 34.187z"></path><path fill="#0074BD" d="M102.123 108.229s3.529 2.91-3.888 5.159c-14.102 4.272-58.706 5.56-71.094.171-4.451-1.938 3.899-4.625 6.526-5.192 2.739-.593 4.303-.485 4.303-.485-4.953-3.487-32.013 6.85-13.743 9.815 49.821 8.076 90.817-3.637 77.896-9.468zM49.912 70.294s-22.686 5.389-8.033 7.348c6.188.828 18.518.638 30.011-.326 9.39-.789 18.813-2.474 18.813-2.474s-3.308 1.419-5.704 3.053c-23.042 6.061-67.544 3.238-54.731-2.958 10.832-5.239 19.644-4.643 19.644-4.643zm40.697 22.747c23.421-12.167 12.591-23.86 5.032-22.285-1.848.385-2.677.72-2.677.72s.688-1.079 2-1.543c14.953-5.255 26.451 15.503-4.823 23.725 0-.002.359-.327.468-.617z"></path><path fill="#EA2D2E" d="M76.491 1.587S89.459 14.563 64.188 34.51c-20.266 16.006-4.621 25.13-.007 35.559-11.831-10.673-20.509-20.07-14.688-28.815C58.041 28.42 81.722 22.195 76.491 1.587z"></path><path fill="#0074BD" d="M52.214 126.021c22.476 1.437 57-.8 57.817-11.436 0 0-1.571 4.032-18.577 7.231-19.186 3.612-42.854 3.191-56.887.874 0 .001 2.875 2.381 17.647 3.331z"></path>
            </svg>
        """,
    "html": """
            <svg viewBox="0 0 128 128">
            <path fill="#E44D26" d="M19.037 113.876L9.032 1.661h109.936l-10.016 112.198-45.019 12.48z"></path><path fill="#F16529" d="M64 116.8l36.378-10.086 8.559-95.878H64z"></path><path fill="#EBEBEB" d="M64 52.455H45.788L44.53 38.361H64V24.599H29.489l.33 3.692 3.382 37.927H64zm0 35.743l-.061.017-15.327-4.14-.979-10.975H33.816l1.928 21.609 28.193 7.826.063-.017z"></path><path fill="#fff" d="M63.952 52.455v13.763h16.947l-1.597 17.849-15.35 4.143v14.319l28.215-7.82.207-2.325 3.234-36.233.335-3.696h-3.708zm0-27.856v13.762h33.244l.276-3.092.628-6.978.329-3.692z"></path>
            </svg>
        """,
    "css": """
            <svg viewBox="0 0 128 128">
            <path fill="#1572B6" d="M18.814 114.123L8.76 1.352h110.48l-10.064 112.754-45.243 12.543-45.119-12.526z"></path><path fill="#33A9DC" d="M64.001 117.062l36.559-10.136 8.601-96.354h-45.16v106.49z"></path><path fill="#fff" d="M64.001 51.429h18.302l1.264-14.163H64.001V23.435h34.682l-.332 3.711-3.4 38.114h-30.95V51.429z"></path><path fill="#EBEBEB" d="M64.083 87.349l-.061.018-15.403-4.159-.985-11.031H33.752l1.937 21.717 28.331 7.863.063-.018v-14.39z"></path><path fill="#fff" d="M81.127 64.675l-1.666 18.522-15.426 4.164v14.39l28.354-7.858.208-2.337 2.406-26.881H81.127z"></path><path fill="#EBEBEB" d="M64.048 23.435v13.831H30.64l-.277-3.108-.63-7.012-.331-3.711h34.646zm-.047 27.996v13.831H48.792l-.277-3.108-.631-7.012-.33-3.711h16.447z"></path>
            </svg>
        """,
    "lua": """
            <svg viewBox="0 0 128 128">
            <path fill="#000080" d="M112.956.708c-7.912 0-14.335 6.424-14.335 14.336s6.424 14.335 14.335 14.335 14.335-6.41 14.335-14.335c0-7.912-6.424-14.336-14.335-14.336zM64 15.058c-27.02 0-48.956 21.935-48.956 48.955S36.979 112.97 64 112.97c27.02 0 48.956-21.935 48.956-48.956 0-27.02-21.936-48.956-48.956-48.956z"></path><path fill="#fff" d="M84.285 29.392c-7.91 0-14.335 6.424-14.335 14.335s6.424 14.336 14.335 14.336 14.336-6.424 14.336-14.336-6.424-14.335-14.335-14.335zM30.773 56.36v32.119h19.961v-3.611H34.87V56.359Zm57.584 8.37c-3.354 0-6.126.975-7.668 2.692-1.055 1.19-1.488 2.516-1.582 4.801h3.705c.311-2.826 1.988-4.098 5.423-4.098 3.3 0 5.153 1.231 5.153 3.435v.974c0 1.542-.92 2.205-3.827 2.556-5.193.663-5.991.839-7.398 1.407-2.69 1.095-4.057 3.164-4.057 6.166 0 4.193 2.908 6.83 7.574 6.83 2.907 0 5.247-1.014 7.843-3.395.257 2.34 1.407 3.395 3.787 3.395.757 0 1.325-.081 2.515-.392v-2.773a2.917 2.917 0 0 1-.798.095c-1.284 0-1.988-.663-1.988-1.812V71.032c0-4.098-3.002-6.302-8.682-6.302zm-33.742.664V83.19c0 3.84 2.867 6.302 7.357 6.302 3.395 0 5.545-1.19 7.709-4.233v3.219h3.3V65.393h-3.652v13.09c0 4.72-2.475 7.804-6.302 7.804-2.907 0-4.76-1.772-4.76-4.544v-16.35Zm38.773 11.67v4.139c0 1.244-.365 1.988-1.46 3.002-1.502 1.366-3.3 2.07-5.464 2.07-2.867 0-4.544-1.367-4.544-3.706 0-2.42 1.636-3.665 5.558-4.233 3.881-.528 4.68-.703 5.91-1.271z"></path><path fill="#808080" d="M61.733 0a64.06 64.06 0 0 0-5.57.436l.179 1.458a62.596 62.596 0 0 1 5.442-.426zm5.585.046-.075 1.468a62.432 62.432 0 0 1 5.433.52L72.88.578a63.91 63.91 0 0 0-5.561-.532Zm-16.665 1.31a63.301 63.301 0 0 0-5.409 1.398l.43 1.405a61.835 61.835 0 0 1 5.284-1.367Zm27.72.237-.33 1.431a62.536 62.536 0 0 1 5.262 1.455l.452-1.397a63.998 63.998 0 0 0-5.384-1.489ZM39.98 4.623a63.447 63.447 0 0 0-5.081 2.323l.668 1.308a61.98 61.98 0 0 1 4.964-2.27zm49.012.41-.573 1.353a62.539 62.539 0 0 1 4.929 2.346l.688-1.298a64.012 64.012 0 0 0-5.044-2.4ZM30.04 9.706a63.95 63.95 0 0 0-4.6 3.17l.886 1.173a62.484 62.484 0 0 1 4.494-3.098zm-8.906 6.728a64.247 64.247 0 0 0-3.983 3.918l1.075 1.001a62.774 62.774 0 0 1 3.891-3.827zm-7.61 8.165a64.04 64.04 0 0 0-3.247 4.546l1.231.8a62.571 62.571 0 0 1 3.172-4.44zm-6.086 9.357a63.459 63.459 0 0 0-2.408 5.042l1.352.574a61.99 61.99 0 0 1 2.352-4.925zm113.623.973-1.31.667a62.616 62.616 0 0 1 2.263 4.967l1.362-.55a64.073 64.073 0 0 0-2.315-5.083zM3.075 44.23a63.382 63.382 0 0 0-1.49 5.385l1.432.328a61.91 61.91 0 0 1 1.455-5.26Zm122.166 1.049-1.404.429a62.513 62.513 0 0 1 1.366 5.285l1.437-.306a63.983 63.983 0 0 0-1.399-5.409zM.574 55.108a64.093 64.093 0 0 0-.528 5.561l1.467.075a62.622 62.622 0 0 1 .516-5.434Zm126.988 1.088-1.458.179a62.465 62.465 0 0 1 .428 5.441l1.468-.05a63.916 63.916 0 0 0-.438-5.57zM1.468 66.205 0 66.255a64.082 64.082 0 0 0 .435 5.57l1.458-.179a62.61 62.61 0 0 1-.425-5.441Zm125.018 1.071a62.63 62.63 0 0 1-.518 5.434l1.455.203a64.16 64.16 0 0 0 .53-5.561zM2.79 77.031l-1.437.304a63.332 63.332 0 0 0 1.398 5.41l1.405-.43A61.864 61.864 0 0 1 2.79 77.03Zm122.188 1.046a61.966 61.966 0 0 1-1.457 5.26l1.397.454a63.43 63.43 0 0 0 1.492-5.384zM5.981 87.459l-1.362.551a63.434 63.434 0 0 0 2.323 5.082l1.307-.669a61.968 61.968 0 0 1-2.268-4.964Zm115.627.99a61.98 61.98 0 0 1-2.354 4.925l1.296.69a63.447 63.447 0 0 0 2.41-5.04zM10.944 97.17l-1.245.78a63.949 63.949 0 0 0 3.17 4.6l1.172-.885a62.481 62.481 0 0 1-3.097-4.495zm105.534.904a62.546 62.546 0 0 1-3.173 4.44l1.156.906a64.024 64.024 0 0 0 3.249-4.545zm-98.96 7.8-1.092.983a64.235 64.235 0 0 0 3.917 3.983l1.002-1.074a62.77 62.77 0 0 1-3.827-3.892zm92.24.79a62.76 62.76 0 0 1-3.893 3.826l.983 1.092a64.221 64.221 0 0 0 3.984-3.916zm-84.263 6.648-.906 1.157a64.026 64.026 0 0 0 4.546 3.248l.8-1.232a62.554 62.554 0 0 1-4.44-3.173zm76.16.654a62.475 62.475 0 0 1-4.495 3.096l.78 1.245a63.945 63.945 0 0 0 4.6-3.17zm-67.018 5.294-.691 1.296a63.45 63.45 0 0 0 5.04 2.409l.575-1.352a61.984 61.984 0 0 1-4.924-2.353zm57.775.496a61.956 61.956 0 0 1-4.964 2.268l.551 1.362a63.425 63.425 0 0 0 5.082-2.322zm-47.74 3.77-.453 1.396a63.419 63.419 0 0 0 5.385 1.49l.329-1.43a61.949 61.949 0 0 1-5.26-1.456zm37.632.322a62.05 62.05 0 0 1-5.284 1.365l.304 1.437a63.361 63.361 0 0 0 5.41-1.398zm-27.003 2.122-.203 1.455a64.093 64.093 0 0 0 5.561.529l.075-1.467a62.605 62.605 0 0 1-5.433-.517zm16.335.139a62.635 62.635 0 0 1-5.442.424l.05 1.468a64.114 64.114 0 0 0 5.57-.434z"></path>
            </svg>
        """,
    "c++": """
            <svg viewBox="0 0 128 128">
                <path fill="#00599c" d="M118.766 95.82c.89-1.543 1.441-3.28 1.441-4.843V36.78c0-1.558-.55-3.297-1.441-4.84l-55.32 31.94Zm0 0"></path>
                <path fill="#004482" d="m68.36 126.586 46.933-27.094c1.352-.781 2.582-2.129 3.473-3.672l-55.32-31.94L8.12 95.82c.89 1.543 2.121 2.89 3.473 3.672l46.933 27.094c2.703 1.562 7.13 1.562 9.832 0Zm0 0"></path>
                <path fill="#659ad2" d="M118.766 31.941c-.891-1.546-2.121-2.894-3.473-3.671L68.359 1.172c-2.703-1.563-7.129-1.563-9.832 0L11.594 28.27C8.89 29.828 6.68 33.66 6.68 36.78v54.196c0 1.562.55 3.3 1.441 4.843L63.445 63.88Zm0 0"></path>
                <path fill="#fff" d="M63.445 26.035c-20.867 0-37.843 16.977-37.843 37.844s16.976 37.844 37.843 37.844c13.465 0 26.024-7.247 32.77-18.91L79.84 73.335c-3.38 5.84-9.66 9.465-16.395 9.465-10.433 0-18.922-8.488-18.922-18.922 0-10.434 8.49-18.922 18.922-18.922 6.73 0 13.017 3.629 16.39 9.465l16.38-9.477c-6.75-11.664-19.305-18.91-32.77-18.91zM92.88 57.57v4.207h-4.207v4.203h4.207v4.207h4.203V65.98h4.203v-4.203h-4.203V57.57H92.88zm15.766 0v4.207h-4.204v4.203h4.204v4.207h4.207V65.98h4.203v-4.203h-4.203V57.57h-4.207z"></path>
            </svg>
        """,
    "bash": """
            <svg viewBox="0 0 128 128">
            <path fill="none" d="M4.24 4.24h119.53v119.53H4.24z"></path><path fill="#293138" d="M109.01 28.64L71.28 6.24c-2.25-1.33-4.77-2-7.28-2s-5.03.67-7.28 2.01l-37.74 22.4c-4.5 2.67-7.28 7.61-7.28 12.96v44.8c0 5.35 2.77 10.29 7.28 12.96l37.73 22.4c2.25 1.34 4.76 2 7.28 2 2.51 0 5.03-.67 7.28-2l37.74-22.4c4.5-2.67 7.28-7.62 7.28-12.96V41.6c0-5.34-2.77-10.29-7.28-12.96zM79.79 98.59l.06 3.22c0 .39-.25.83-.55.99l-1.91 1.1c-.3.15-.56-.03-.56-.42l-.03-3.17c-1.63.68-3.29.84-4.34.42-.2-.08-.29-.37-.21-.71l.69-2.91c.06-.23.18-.46.34-.6.06-.06.12-.1.18-.13.11-.06.22-.07.31-.03 1.14.38 2.59.2 3.99-.5 1.78-.9 2.97-2.72 2.95-4.52-.02-1.64-.9-2.31-3.05-2.33-2.74.01-5.3-.53-5.34-4.57-.03-3.32 1.69-6.78 4.43-8.96l-.03-3.25c0-.4.24-.84.55-1l1.85-1.18c.3-.15.56.04.56.43l.03 3.25c1.36-.54 2.54-.69 3.61-.44.23.06.34.38.24.75l-.72 2.88c-.06.22-.18.44-.33.58a.77.77 0 01-.19.14c-.1.05-.19.06-.28.05-.49-.11-1.65-.36-3.48.56-1.92.97-2.59 2.64-2.58 3.88.02 1.48.77 1.93 3.39 1.97 3.49.06 4.99 1.58 5.03 5.09.05 3.44-1.79 7.15-4.61 9.41zm26.34-60.5l-35.7 22.05c-4.45 2.6-7.73 5.52-7.74 10.89v43.99c0 3.21 1.3 5.29 3.29 5.9-.65.11-1.32.19-1.98.19-2.09 0-4.15-.57-5.96-1.64l-37.73-22.4c-3.69-2.19-5.98-6.28-5.98-10.67V41.6c0-4.39 2.29-8.48 5.98-10.67l37.74-22.4c1.81-1.07 3.87-1.64 5.96-1.64s4.15.57 5.96 1.64l37.74 22.4c3.11 1.85 5.21 5.04 5.8 8.63-1.27-2.67-4.09-3.39-7.38-1.47z"></path><path fill="#4FA847" d="M99.12 90.73l-9.4 5.62c-.25.15-.43.31-.43.61v2.46c0 .3.2.43.45.28l9.54-5.8c.25-.15.29-.42.29-.72v-2.17c0-.3-.2-.42-.45-.28z"></path>
            </svg>
        """,
    "powershell": """
            <svg viewBox="0 0 128 128">
            <linearGradient id="a" x1="96.306" x2="25.454" y1="35.144" y2="98.431" gradientTransform="matrix(1 0 0 -1 0 128)" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#a9c8ff"></stop><stop offset="1" stop-color="#c7e6ff"></stop></linearGradient><path fill="url(#a)" fill-rule="evenodd" d="M7.2 110.5c-1.7 0-3.1-.7-4.1-1.9-1-1.2-1.3-2.9-.9-4.6l18.6-80.5c.8-3.4 4-6 7.4-6h92.6c1.7 0 3.1.7 4.1 1.9 1 1.2 1.3 2.9.9 4.6l-18.6 80.5c-.8 3.4-4 6-7.4 6H7.2z" clip-rule="evenodd" opacity=".8"></path><linearGradient id="b" x1="25.336" x2="94.569" y1="98.33" y2="36.847" gradientTransform="matrix(1 0 0 -1 0 128)" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#2d4664"></stop><stop offset=".169" stop-color="#29405b"></stop><stop offset=".445" stop-color="#1e2f43"></stop><stop offset=".79" stop-color="#0c131b"></stop><stop offset="1"></stop></linearGradient><path fill="url(#b)" fill-rule="evenodd" d="M120.3 18.5H28.5c-2.9 0-5.7 2.3-6.4 5.2L3.7 104.3c-.7 2.9 1.1 5.2 4 5.2h91.8c2.9 0 5.7-2.3 6.4-5.2l18.4-80.5c.7-2.9-1.1-5.3-4-5.3z" clip-rule="evenodd"></path><path fill="#2C5591" fill-rule="evenodd" d="M64.2 88.3h22.3c2.6 0 4.7 2.2 4.7 4.9s-2.1 4.9-4.7 4.9H64.2c-2.6 0-4.7-2.2-4.7-4.9s2.1-4.9 4.7-4.9zM78.7 66.5c-.4.8-1.2 1.6-2.6 2.6L34.6 98.9c-2.3 1.6-5.5 1-7.3-1.4-1.7-2.4-1.3-5.7.9-7.3l37.4-27.1v-.6l-23.5-25c-1.9-2-1.7-5.3.4-7.4 2.2-2 5.5-2 7.4 0l28.2 30c1.7 1.9 1.8 4.5.6 6.4z" clip-rule="evenodd"></path><path fill="#FFF" fill-rule="evenodd" d="M77.6 65.5c-.4.8-1.2 1.6-2.6 2.6L33.6 97.9c-2.3 1.6-5.5 1-7.3-1.4-1.7-2.4-1.3-5.7.9-7.3l37.4-27.1v-.6l-23.5-25c-1.9-2-1.7-5.3.4-7.4 2.2-2 5.5-2 7.4 0l28.2 30c1.7 1.8 1.8 4.4.5 6.4zM63.5 87.8h22.3c2.6 0 4.7 2.1 4.7 4.6 0 2.6-2.1 4.6-4.7 4.6H63.5c-2.6 0-4.7-2.1-4.7-4.6 0-2.6 2.1-4.6 4.7-4.6z" clip-rule="evenodd"></path>
            </svg>
        """,
    "c#": """
            <svg viewBox="0 0 128 128">
            <path fill="#9B4F96" d="M115.4 30.7L67.1 2.9c-.8-.5-1.9-.7-3.1-.7-1.2 0-2.3.3-3.1.7l-48 27.9c-1.7 1-2.9 3.5-2.9 5.4v55.7c0 1.1.2 2.4 1 3.5l106.8-62c-.6-1.2-1.5-2.1-2.4-2.7z"></path><path fill="#68217A" d="M10.7 95.3c.5.8 1.2 1.5 1.9 1.9l48.2 27.9c.8.5 1.9.7 3.1.7 1.2 0 2.3-.3 3.1-.7l48-27.9c1.7-1 2.9-3.5 2.9-5.4V36.1c0-.9-.1-1.9-.6-2.8l-106.6 62z"></path><path fill="#fff" d="M85.3 76.1C81.1 83.5 73.1 88.5 64 88.5c-13.5 0-24.5-11-24.5-24.5s11-24.5 24.5-24.5c9.1 0 17.1 5 21.3 12.5l13-7.5c-6.8-11.9-19.6-20-34.3-20-21.8 0-39.5 17.7-39.5 39.5s17.7 39.5 39.5 39.5c14.6 0 27.4-8 34.2-19.8l-12.9-7.6zM97 66.2l.9-4.3h-4.2v-4.7h5.1L100 51h4.9l-1.2 6.1h3.8l1.2-6.1h4.8l-1.2 6.1h2.4v4.7h-3.3l-.9 4.3h4.2v4.7h-5.1l-1.2 6h-4.9l1.2-6h-3.8l-1.2 6h-4.8l1.2-6h-2.4v-4.7H97zm4.8 0h3.8l.9-4.3h-3.8l-.9 4.3z"></path>
            </svg>
        """,
    "typescript": """
            <svg viewBox="0 0 128 128">
            <path fill="#fff" d="M22.67 47h99.67v73.67H22.67z"></path><path data-name="original" fill="#007acc" d="M1.5 63.91v62.5h125v-125H1.5zm100.73-5a15.56 15.56 0 017.82 4.5 20.58 20.58 0 013 4c0 .16-5.4 3.81-8.69 5.85-.12.08-.6-.44-1.13-1.23a7.09 7.09 0 00-5.87-3.53c-3.79-.26-6.23 1.73-6.21 5a4.58 4.58 0 00.54 2.34c.83 1.73 2.38 2.76 7.24 4.86 8.95 3.85 12.78 6.39 15.16 10 2.66 4 3.25 10.46 1.45 15.24-2 5.2-6.9 8.73-13.83 9.9a38.32 38.32 0 01-9.52-.1 23 23 0 01-12.72-6.63c-1.15-1.27-3.39-4.58-3.25-4.82a9.34 9.34 0 011.15-.73L82 101l3.59-2.08.75 1.11a16.78 16.78 0 004.74 4.54c4 2.1 9.46 1.81 12.16-.62a5.43 5.43 0 00.69-6.92c-1-1.39-3-2.56-8.59-5-6.45-2.78-9.23-4.5-11.77-7.24a16.48 16.48 0 01-3.43-6.25 25 25 0 01-.22-8c1.33-6.23 6-10.58 12.82-11.87a31.66 31.66 0 019.49.26zm-29.34 5.24v5.12H56.66v46.23H45.15V69.26H28.88v-5a49.19 49.19 0 01.12-5.17C29.08 59 39 59 51 59h21.83z"></path>
            </svg>
        """,
    "php": """
            <svg viewBox="0 0 128 128">
            <path fill="url(#a)" d="M0 64c0 18.593 28.654 33.667 64 33.667 35.346 0 64-15.074 64-33.667 0-18.593-28.655-33.667-64-33.667C28.654 30.333 0 45.407 0 64Z"></path><path fill="#777bb3" d="M64 95.167c33.965 0 61.5-13.955 61.5-31.167 0-17.214-27.535-31.167-61.5-31.167S2.5 46.786 2.5 64c0 17.212 27.535 31.167 61.5 31.167Z"></path><path d="M34.772 67.864c2.793 0 4.877-.515 6.196-1.53 1.306-1.006 2.207-2.747 2.68-5.175.44-2.27.272-3.854-.5-4.71-.788-.874-2.493-1.317-5.067-1.317h-4.464l-2.473 12.732zM20.173 83.547a.694.694 0 0 1-.68-.828l6.557-33.738a.695.695 0 0 1 .68-.561h14.134c4.442 0 7.748 1.206 9.827 3.585 2.088 2.39 2.734 5.734 1.917 9.935-.333 1.711-.905 3.3-1.7 4.724a15.818 15.818 0 0 1-3.128 3.92c-1.531 1.432-3.264 2.472-5.147 3.083-1.852.604-4.232.91-7.07.91h-5.724l-1.634 8.408a.695.695 0 0 1-.682.562z"></path><path fill="#fff" d="M34.19 55.826h3.891c3.107 0 4.186.682 4.553 1.089.607.674.723 2.097.331 4.112-.439 2.257-1.253 3.858-2.42 4.756-1.194.92-3.138 1.386-5.773 1.386h-2.786l2.205-11.342zm6.674-8.1H26.731a1.39 1.39 0 0 0-1.364 1.123L18.81 82.588a1.39 1.39 0 0 0 1.363 1.653h7.35a1.39 1.39 0 0 0 1.363-1.124l1.525-7.846h5.151c2.912 0 5.364-.318 7.287-.944 1.977-.642 3.796-1.731 5.406-3.237a16.522 16.522 0 0 0 3.259-4.087c.831-1.487 1.429-3.147 1.775-4.931.86-4.423.161-7.964-2.076-10.524-2.216-2.537-5.698-3.823-10.349-3.823zM30.301 68.557h4.471c2.963 0 5.17-.557 6.62-1.675 1.451-1.116 2.428-2.98 2.938-5.591.485-2.508.264-4.277-.665-5.308-.931-1.03-2.791-1.546-5.584-1.546h-5.036l-2.743 14.12m10.563-19.445c4.252 0 7.353 1.117 9.303 3.348 1.95 2.232 2.536 5.347 1.76 9.346-.322 1.648-.863 3.154-1.625 4.518-.764 1.366-1.76 2.614-2.991 3.747-1.468 1.373-3.097 2.352-4.892 2.935-1.794.584-4.08.875-6.857.875h-6.296l-1.743 8.97h-7.35l6.558-33.739h14.133"></path><path d="M69.459 74.577a.694.694 0 0 1-.682-.827l2.9-14.928c.277-1.42.209-2.438-.19-2.87-.245-.263-.979-.704-3.15-.704h-5.256l-3.646 18.768a.695.695 0 0 1-.683.56h-7.29a.695.695 0 0 1-.683-.826l6.558-33.739a.695.695 0 0 1 .682-.561h7.29a.695.695 0 0 1 .683.826L64.41 48.42h5.653c4.307 0 7.227.758 8.928 2.321 1.733 1.593 2.275 4.14 1.608 7.573l-3.051 15.702a.695.695 0 0 1-.682.56h-7.407z"></path><path fill="#fff" d="M65.31 38.755h-7.291a1.39 1.39 0 0 0-1.364 1.124l-6.557 33.738a1.39 1.39 0 0 0 1.363 1.654h7.291a1.39 1.39 0 0 0 1.364-1.124l3.537-18.205h4.682c2.168 0 2.624.463 2.641.484.132.14.305.795.019 2.264l-2.9 14.927a1.39 1.39 0 0 0 1.364 1.654h7.408a1.39 1.39 0 0 0 1.363-1.124l3.051-15.7c.715-3.686.103-6.45-1.82-8.217-1.836-1.686-4.91-2.505-9.398-2.505h-4.81l1.421-7.315a1.39 1.39 0 0 0-1.364-1.655zm0 1.39-1.743 8.968h6.496c4.087 0 6.907.714 8.457 2.14 1.553 1.426 2.017 3.735 1.398 6.93l-3.052 15.699h-7.407l2.901-14.928c.33-1.698.208-2.856-.365-3.474-.573-.617-1.793-.926-3.658-.926h-5.829l-3.756 19.327H51.46l6.558-33.739h7.292z"></path><path d="M92.136 67.864c2.793 0 4.878-.515 6.198-1.53 1.304-1.006 2.206-2.747 2.679-5.175.44-2.27.273-3.854-.5-4.71-.788-.874-2.493-1.317-5.067-1.317h-4.463l-2.475 12.732zM77.54 83.547a.694.694 0 0 1-.682-.828l6.557-33.738a.695.695 0 0 1 .682-.561H98.23c4.442 0 7.748 1.206 9.826 3.585 2.089 2.39 2.734 5.734 1.917 9.935a15.878 15.878 0 0 1-1.699 4.724 15.838 15.838 0 0 1-3.128 3.92c-1.53 1.432-3.265 2.472-5.147 3.083-1.852.604-4.232.91-7.071.91h-5.723l-1.633 8.408a.695.695 0 0 1-.683.562z"></path><path fill="#fff" d="M91.555 55.826h3.891c3.107 0 4.186.682 4.552 1.089.61.674.724 2.097.333 4.112-.44 2.257-1.254 3.858-2.421 4.756-1.195.92-3.139 1.386-5.773 1.386h-2.786l2.204-11.342zm6.674-8.1H84.096a1.39 1.39 0 0 0-1.363 1.123l-6.558 33.739a1.39 1.39 0 0 0 1.364 1.653h7.35a1.39 1.39 0 0 0 1.363-1.124l1.525-7.846h5.15c2.911 0 5.364-.318 7.286-.944 1.978-.642 3.797-1.731 5.408-3.238a16.52 16.52 0 0 0 3.258-4.086c.832-1.487 1.428-3.147 1.775-4.931.86-4.423.162-7.964-2.076-10.524-2.216-2.537-5.697-3.823-10.35-3.823zM87.666 68.557h4.47c2.964 0 5.17-.557 6.622-1.675 1.45-1.116 2.428-2.98 2.936-5.591.487-2.508.266-4.277-.665-5.308-.93-1.03-2.791-1.546-5.583-1.546h-5.035Zm10.563-19.445c4.251 0 7.354 1.117 9.303 3.348 1.95 2.232 2.537 5.347 1.759 9.346-.32 1.648-.862 3.154-1.624 4.518-.763 1.366-1.76 2.614-2.992 3.747-1.467 1.373-3.097 2.352-4.892 2.935-1.793.584-4.078.875-6.856.875h-6.295l-1.745 8.97h-7.35l6.558-33.739h14.133"></path><defs><radialGradient id="a" cx="0" cy="0" r="1" gradientTransform="matrix(84.04136 0 0 84.04136 38.426 42.169)" gradientUnits="userSpaceOnUse"><stop stop-color="#AEB2D5"></stop><stop offset=".3" stop-color="#AEB2D5"></stop><stop offset=".75" stop-color="#484C89"></stop><stop offset="1" stop-color="#484C89"></stop></radialGradient></defs>
            </svg>
        """,
    
}


@logfire.instrument("Creating yaml stream of colors", extract_args=False)
def ordered_load(stream: str|bool, Loader: yaml.Loader=yaml.Loader, object_pairs_hook: OrderedDict=OrderedDict) -> any:
    """
    Parse the first YAML document in a stream
    and produce the corresponding Python Orderered Dictionary.
    """
    class OrderedLoader(Loader):
        pass
    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        lambda loader, node: object_pairs_hook(loader.construct_pairs(node)))
    
    return yaml.load(stream, OrderedLoader)


def order_by_keys(dict: dict) -> OrderedDict:
    """
    Sort a dictionary by keys, case insensitive ie [ Ada, eC, Fortran ]
    Default ordering, or using json.dump with sort_keys=True, produces
    [ Ada, Fortran, eC ]
    """
    logfire.info("Sorting dictionary by keys")
    return OrderedDict(sorted(dict.items(), key=lambda s: s[0].lower()))

@logfire.instrument("Getting file from URL")
def get_file(url: str) -> str | bool:
    """
    Return the URL body, or False if page not found

    Keyword arguments:
    url -- url to parse
    """
    try:
        r = requests.get(url)
    except requests.exceptions.RequestException as error:
        logfire.fatal(f"Request fatal error: {error}")
        sys.exit(1)

    if r.status_code != 200:
        logfire.error(f"Request error page not found. Response code: {r.status_code}")
        return False

    logfire.info("Request successful")
    return r.text

def is_dark(color: str) -> bool:
    l = 0.2126 * int(color[0:2], 16) + 0.7152 * int(color[2:4], 16) + 0.0722 * int(color[4:6], 16)
    return False if l / 255 > 0.65 else True

@logfire.instrument("Getting colors of all programming languages on GitHub")
def run():
    # Get list of all langs
    logfire.info("Getting colors")
    yml = get_file("https://raw.githubusercontent.com/github/linguist/master/"
                   "lib/linguist/languages.yml")
    langs_yml = ordered_load(yml)
    langs_yml = order_by_keys(langs_yml)

    # List construction done, count keys
    lang_count = len(langs_yml)
    logfire.info("Found %d languages" % lang_count)

    # Construct the wanted list
    langs = OrderedDict()
    logfire.info("Creating dictionary of colors")
    for lang in langs_yml.keys():
        if ("type" not in langs_yml[lang] or
                "color" in langs_yml[lang] or
                langs_yml[lang]["type"] == "programming"):
            langs[lang] = OrderedDict()
            langs[lang]["color"] = langs_yml[lang]["color"] if "color" in langs_yml[lang] else None
            langs[lang]["url"] = "https://github.com/trending?l=" + (langs_yml[lang]["search_term"] if "search_term" in langs_yml[lang] else lang)
            langs[lang]["url"] = langs[lang]["url"].replace(' ','-').replace('#','sharp')
            langs[lang]["svg"] = SVGS[lang.lower()] if lang.lower() in SVGS.keys() else ""
    
    logfire.info(f"Processed {len(langs)} languages")
    return langs
