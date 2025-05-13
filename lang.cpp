ignoreUnregisteredUsers = settings->value(\"chat/ignore_unregistered\", false).toBool();
{
attemptAutoConnect = settings->value(\"server/auto_connect\", 0).toInt() == 0 ? false : true; 
}
void SettingsCache::setLang(const QString &_lang)
