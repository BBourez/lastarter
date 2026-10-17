<#ftl output_format="HTML">
<#-- LaStarter - template maitre du theme SSO.
     Layout deux colonnes : gauche 75% (branding), droite 25% (formulaire).
     Les pages (login.ftl, etc.) appellent registrationLayout et rendent
     leurs sections "header" et "form" dans la colonne de droite. -->

<#macro registrationLayout displayMessage=true displayInfo=false displayRequiredFields=false displayWide=false>
    <!doctype html>
    <html lang="${(locale.currentLanguageTag)!"fr"}">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta name="robots" content="noindex, nofollow">
        <title>${msg("loginTitle", (realm.displayName!"LaStarter"))}</title>
        <link rel="icon" href="${url.resourcesPath}/img/favicon.ico">
        <#if properties.styles?has_content>
            <#list properties.styles?split(" ") as style>
                <link href="${url.resourcesPath}/${style}" rel="stylesheet">
            </#list>
        </#if>
        <#if scripts??>
            <#list scripts as script>
                <script src="${script}" type="text/javascript"></script>
            </#list>
        </#if>
    </head>

    <body class="ls-sso-body">
        <div class="ls-sso-shell">

            <!-- ============ COLONNE GAUCHE : 75% branding (visuel seul) ============ -->
            <div class="ls-sso-left"></div>

            <!-- ============ COLONNE DROITE : 25% formulaire ============ -->
            <div class="ls-sso-right">
                <div class="ls-sso-card">

                    <#-- Messages globaux (erreur, info) -->
                    <#if displayMessage && message?has_content && message.summary?has_content>
                        <div class="ls-message ls-message-${message.type}">
                            ${kcSanitize(message.summary)?no_esc}
                        </div>
                    </#if>

                    <header class="ls-sso-card-header">
                        <h2><#nested "header"></h2>
                    </header>

                    <div class="ls-sso-card-body">
                        <#nested "form">
                    </div>

                    <#if displayInfo>
                        <div class="ls-sso-card-info">
                            <#nested "info">
                        </div>
                    </#if>
                </div>
            </div>
        </div>
    </body>
    </html>
</#macro>
