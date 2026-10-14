<#ftl output_format="HTML">
<#-- LaStarter — login split-screen (style Element Call).
     Hérite des macros du parent keycloak pour les champs (kc-register-form,
     kc-username, etc.) mais surcharge le layout : panneau gauche dégradé
     vert sombre avec la marque, panneau droit avec le formulaire. -->
<#import "template.ftl" as layout>
<@layout.registrationLayout displayMessage=!messagesPerField.existsError('username','password','registrationUserAcl'); section>
    <#if section = "header">
        ${msg("loginAccountTitle")}
    <#elseif section = "form">
        <div id="kc-form">
            <div id="kc-form-wrapper">
                <#if realm.password>
                    <form id="kc-form-login" onsubmit="login.disabled = true; return true;" action="${url.loginAction}" method="post">
                        <div class="ls-field">
                            <label for="username">${msg("username")}</label>
                            <input id="username" name="username" type="text" autofocus autocomplete="username"
                                   value="${(login.username!'')}"
                                   aria-invalid="<#if messagesPerField.existsError('username','password')>true</#if>"/>
                            <#if messagesPerField.existsError('username','password')>
                                <span class="ls-error">${kcSanitize(messagesPerField.getFirstError('username','password'))?no_esc}</span>
                            </#if>
                        </div>

                        <div class="ls-field">
                            <label for="password">${msg("password")}</label>
                            <input id="password" name="password" type="password" autocomplete="current-password"
                                   aria-invalid="<#if messagesPerField.existsError('username','password')>true</#if>"/>
                        </div>

                        <div class="ls-field ls-field-actions">
                            <div id="kc-form-options">
                                <#if realm.rememberMe>
                                    <div class="ls-checkbox">
                                        <label>
                                            <#if login.rememberMe??>
                                                <input id="rememberMe" name="rememberMe" type="checkbox" tabindex="3" checked>
                                            <#else>
                                                <input id="rememberMe" name="rememberMe" type="checkbox" tabindex="3">
                                            </#if>
                                            ${msg("rememberMe")}
                                        </label>
                                    </div>
                                </#if>
                            </div>
                            <div id="kc-form-buttons" class="ls-submit">
                                <input type="hidden" id="id-hidden-input" name="credentialId" <#if auth??.selectedCredential?has_content>value="${auth.selectedCredential}"</#if>/>
                                <button type="submit" class="ls-btn-primary">${msg("doLogIn")}</button>
                            </div>
                        </div>
                    </form>

                    <div class="ls-links">
                        <#if realm.resetPasswordAllowed>
                            <a href="${url.loginResetCredentialsUrl}">${msg("doForgotPassword")}</a>
                        </#if>
                        <#if realm.registrationAllowed && !realm.registrationEmailAsUsername>
                            <span>${msg("noAccount")} <a href="${url.registrationUrl}">${msg("doRegister")}</a></span>
                        </#if>
                    </div>
                </#if>
            </div>
        </div>
        <script type="module">
            // Focus automatique sur le premier champ.
            const first = document.getElementById("username") || document.getElementById("password");
            if (first) first.focus();
        </script>
    </#if>
</@layout.registrationLayout>
