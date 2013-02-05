Test.Summary='''
Basic test for making sure WDK works
'''

Test.SkipUnless(
    Condition.IsPlatform('windows'),
     Condition.HasRegKey(
                    HKEY_CURRENT_USER,
                    [r'Software\Microsoft\KitSetup\configured-kits',
                     r'Software\Wow6432Node\Microsoft\KitSetup'],
                    "WDK not installed on the system"
                   )
    )
Setup.Copy.FromSample('wdk')

Test.AddBuildRun()


